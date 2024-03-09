from web3 import Web3
from web3._utils.filters import construct_event_filter_params, Filter
from web3._utils.events import get_event_data
from web3.types import LogReceipt, EventData
from typing import Final, Any
from web3.contract.base_contract import BaseContractEvent
from eth_abi.codec import ABICodec


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

# Only define the function symbol (gets the symbol of a token)
TOKEN_SYMBOL_ABI: Final[list[dict[str, Any]]] = [
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
    }
]


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
        logs (list[LogReceipt]): The logs to parse

    Returns:
        list[EventData]: The parsed logs
    """
    all_events = []
    for log in logs:
        event = get_event_data(codec, approval_event.abi, log)
        all_events.append(event)

    return all_events


def get_contract_token_symbol(w3: Web3, contract_address: str) -> str:
    """
    Returns the token's symbol of the given contract address

    Args:
        contract_address (str): The address of the contract

    Returns:
        str: The symbol of the token
    """

    contract = w3.eth.contract(contract_address, abi=TOKEN_SYMBOL_ABI)

    token_symbol = contract.functions.symbol().call()
    return token_symbol


def print_approvals_of_owner(w3: Web3, owner_address: str):
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
        token_symbol = get_contract_token_symbol(
            w3=w3, contract_address=approval.address
        )
        print(f"approval on {token_symbol} on amount of {approval.args.value}")
