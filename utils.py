from web3 import Web3
from web3._utils.filters import construct_event_filter_params, Filter
from web3._utils.events import get_event_data
from web3.types import LogReceipt, EventData
from typing import Final, Any
from web3.contract.base_contract import BaseContractEvent
from eth_abi.codec import ABICodec
import requests
from requests import Response


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

# Only define the symbol and name functions
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
]

COINGECKO_URL: Final[str] = "https://api.coingecko.com/api/v3/simple/price"


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


def get_contract_token_name_and_symbol(
    w3: Web3, contract_address: str
) -> tuple[str, str]:
    """
    Returns the token's name and symbol of the given contract address

    Args:
        w3 (Web3): The web3 API
        contract_address (str): The address of the contract

    Returns:
        tuple[str, str]: (name, symbol) of the given token
    """

    contract = w3.eth.contract(contract_address, abi=TOKEN_DATA_ABI)

    token_name = contract.functions.name().call()
    token_symbol = contract.functions.symbol().call()
    return token_name, token_symbol


def print_approvals_of_owner(w3: Web3, owner_address: str):
    """
    Print the approvals of an owner address in the format of:
    approval on {token_symbol} on amount of {approval_amount}

    Args:
        w3 (Web3): The web3 API
        owner_address (str): The owner address that approved
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
    for approval in parsed_approvals:
        token_name, token_symbol = get_contract_token_name_and_symbol(
            w3=w3, contract_address=approval.address
        )
        token_price = get_token_price(token_name=token_name, token_symbol=token_symbol)
        print(
            f"approval on {token_symbol} on amount of {approval.args.value} --- Token's price = {token_price} USD"
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
