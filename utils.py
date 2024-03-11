from web3 import Web3
from web3._utils.filters import construct_event_filter_params, Filter
from web3._utils.events import get_event_data
from web3.types import LogReceipt, EventData
from typing import Final, Any, Callable
from web3.contract.base_contract import BaseContractEvent
from eth_abi.codec import ABICodec
import requests
from requests import Response
from dataclasses import dataclass
import math


# Only Approval event
APPROVALS_ABI: Final[list[dict[str, Any]]] = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "owner", "type": "address"},
            {"indexed": True, "name": "spender", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"},
        ],
        "name": "Approval",
        "type": "event",
    }
]

# Only define the symbol and name and balanceOf functions
TOKEN_DATA_ABI: Final[list[dict[str, Any]]] = [
    {
        "inputs": [],
        "name": "name",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "payable": False,
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
]

COINGECKO_URL: Final[str] = "https://api.coingecko.com/api/v3/simple/price"


@dataclass
class TokenData:
    """
    A dataclass that represents the data we need on a token
    """

    name: str
    symbol: str
    balanceOf_function: Callable
    decimals: int


@dataclass
class ApprovalData:
    """
    A dataclass that represents the data we need to return about an approval
    """

    token_name: str
    token_symbol: str
    approval_amount: float
    token_price: float | None
    exposure: float
    exposure_usd: float | None  # This field is None if the token_price is None


def get_web3_api() -> Web3:
    """
    Gets a web3 API object that can query the infura API

    Returns:
        Web3: The web3 API
    """

    mainnet_url = "mainnet.infura.io/v3"
    with open("api_key.txt", "r") as key_file:
        api_key = key_file.read()

    provider_url = f"{mainnet_url}/{api_key}"
    w3 = Web3(Web3.HTTPProvider(f"https://{provider_url}"))
    return w3


def get_approvals_of_owner_filter(
    w3: Web3,
    approval_event: type[BaseContractEvent],
    codec: ABICodec,
    owner_address: str,
) -> Filter:
    """
    Returns a filter of the approvals that the given owner approved

    Args:
        w3 (Web3): The web3 API
        approval_event (type[BaseContractEvent]): The approval event with the approval abi in it
        codec (ABICodec): The eth codec
        owner_address (str): The owner address that approved

    Returns:
        Filter: A filter of the approvals that the given owner approved
    """

    _, approval_filter_params = construct_event_filter_params(
        approval_event.abi,
        codec,
        argument_filters={"owner": owner_address},
        # Start the filter from block 0 so that all of the records will be viewed by the filter
        fromBlock=0,
    )

    return w3.eth.filter(approval_filter_params)


def parse_approval_logs(
    approval_event: type[BaseContractEvent], codec: ABICodec, logs: list[LogReceipt]
) -> list[EventData]:
    """
    Parse the raw binary logs to python proxy objects as described by the APPROVALS_ABI

    Args:
        approval_event (type[BaseContractEvent]): The approval event with the approval abi in it
        codec (ABICodec): The eth codec
        logs (list[LogReceipt]): The logs to parse

    Returns:
        list[EventData]: The parsed logs
    """
    all_events = []
    for log in logs:
        event = get_event_data(codec, approval_event.abi, log)
        all_events.append(event)

    return all_events


def get_contract_token_data(w3: Web3, contract_address: str) -> TokenData:
    """
    Returns the token's data of the given contract address

    Args:
        w3 (Web3): The web3 API
        contract_address (str): The address of the contract

    Returns:
        TokenData: The data of the given token
    """

    contract = w3.eth.contract(contract_address, abi=TOKEN_DATA_ABI)

    token_name = contract.functions.name().call()
    token_symbol = contract.functions.symbol().call()
    token_balanceOf_function = contract.functions.balanceOf
    token_decimals = int(contract.functions.decimals().call())

    return TokenData(
        name=token_name,
        symbol=token_symbol,
        balanceOf_function=token_balanceOf_function,
        decimals=token_decimals,
    )


def get_approvals_data_of_owner(w3: Web3, owner_address: str) -> list[ApprovalData]:
    """
    Returns a list of approvals data of the given owner

    Args:
        w3 (Web3): The web3 API
        owner_address (str): The owner address that approved

    Returns:
        list[ApprovalData]: Approvals data of the given owner
    """

    approval_contract = w3.eth.contract(abi=APPROVALS_ABI)

    approval_event = approval_contract.events.Approval()
    codec = w3.codec

    approvals_filter = get_approvals_of_owner_filter(
        w3=w3, approval_event=approval_event, codec=codec, owner_address=owner_address
    )
    logs = approvals_filter.get_all_entries()
    parsed_approvals = parse_approval_logs(
        approval_event=approval_event, codec=codec, logs=logs
    )

    all_approvals_data = []
    for approval in parsed_approvals:
        approve_amount = int(approval.args.value)
        token_data = get_contract_token_data(w3=w3, contract_address=approval.address)
        approve_amount = approve_amount / math.pow(10, token_data.decimals)

        balance = int(token_data.balanceOf_function(owner_address).call())
        balance = balance / math.pow(10, token_data.decimals)
        exposure = min(approve_amount, balance)

        token_price = get_token_price(
            token_name=token_data.name, token_symbol=token_data.symbol
        )

        exposure_usd = exposure * token_price if token_price else None
        approval_data = ApprovalData(
            token_name=token_data.name,
            token_symbol=token_data.symbol,
            approval_amount=approve_amount,
            token_price=token_price,
            exposure=exposure,
            exposure_usd=exposure_usd,
        )
        all_approvals_data.append(approval_data)

    return all_approvals_data


def print_approvals_of_owner(w3: Web3, owner_address: str):
    """
    Print the approvals of an owner address in the format of:
    approval on {token_symbol} on amount of {approval_amount}

    Args:
        w3 (Web3): The web3 API
        owner_address (str): The owner address that approved
    """

    all_approvals_data = get_approvals_data_of_owner(w3=w3, owner_address=owner_address)

    for approval_data in all_approvals_data:
        if approval_data.token_price:
            exposure_str = f"{approval_data.exposure_usd} USD"
            token_price_str = f"{approval_data.token_price} USD"
        else:
            exposure_str = f"{approval_data.exposure} (No token price found)"
            token_price_str = "None"

        print(
            f"approval on {approval_data.token_symbol} on amount of {approval_data.approval_amount} --- Token's price = {token_price_str} --- exposure = {exposure_str}"
        )


def _get_token_price_from_response(response: Response, search_key: str) -> str | None:
    """
    Returns the token's price from the response

    Args:
        response (Response): The response of coingecko api
        search_key (str): The key we searched by in the api

    Returns:
        str | None: The token price or None if not found
    """

    token_price = None
    if response.status_code == 200:
        response_data = response.json()
        if search_key in response_data:
            if "usd" in response_data[search_key]:
                token_price = response_data[search_key]["usd"]
    return token_price


def get_token_price(token_name: str, token_symbol: str) -> str | None:
    """
    Returns the given token's price in USD

    Args:
        token_symbol (str): The token's symbol

    Returns:
        str | None: The token's price if found or None otherwise
    """

    token_name = token_name.lower()
    token_symbol = token_symbol.lower()
    search_by_name_params = {"ids": token_name, "vs_currencies": "USD"}
    search_by_symbol_params = {"ids": token_symbol, "vs_currencies": "USD"}
    response_by_name = requests.get(COINGECKO_URL, params=search_by_name_params)
    token_price = _get_token_price_from_response(
        response=response_by_name, search_key=token_name
    )
    if token_price:
        return token_price
    else:
        response_by_symbol = requests.get(COINGECKO_URL, params=search_by_symbol_params)
        return _get_token_price_from_response(
            response=response_by_symbol, search_key=token_symbol
        )
