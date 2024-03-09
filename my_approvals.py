import argparse
from web3 import Web3
from web3.types import FilterParams
from web3._utils.filters import construct_event_filter_params
from web3._utils.events import get_event_data
import json
from web3.datastructures import AttributeDict

parser = argparse.ArgumentParser(description="Get all approvals for an address on the blockchain.")
parser.add_argument("--address", type=str, required=True, help="The address on the blockchain to get approvals of.")

args = parser.parse_args()
address = int(args.address, base=0)

mainnet_url = "mainnet.infura.io/v3"
with open("api_key.txt", "r") as key_file:
    api_key = key_file.read()

provider_url = f"{mainnet_url}/{api_key}"
w3 = Web3(Web3.HTTPProvider(f"https://{provider_url}"))




# Reduced ERC-20 ABI, only Approval event
ABI = """[
    {
        "anonymous": false,
        "inputs": [
            {
                "indexed": true,
                "name": "owner",
                "type": "address"
            },
            {
                "indexed": true,
                "name": "spender",
                "type": "address"
            },
            {
                "indexed": false,
                "name": "value",
                "type": "uint256"
            }
        ],
        "name": "Approval",
        "type": "event"
    }
]
"""

abi = json.loads(ABI)
ERC20 = w3.eth.contract(abi=abi)

event = ERC20.events.Approval()
codec = w3.codec

data_filter_set, event_filter_params = construct_event_filter_params(
    event.abi,
    codec,
    argument_filters={"owner": address},
    fromBlock=0
)


approvals_filter = w3.eth.filter(event_filter_params)
logs = approvals_filter.get_all_entries()

# Convert raw binary data to Python proxy objects as described by ABI
all_events = []
for log in logs:
    # Convert raw JSON-RPC log result to human readable event by using ABI data
    # More information how process_log works here
    # https://github.com/ethereum/web3.py/blob/fbaf1ad11b0c7fac09ba34baff2c256cffe0a148/web3/_utils/events.py#L200
    evt = get_event_data(codec, event.abi, log)
    # Note: This was originally yield,
    # but deferring the timeout exception caused the throttle logic not to work
    all_events.append(evt)

print(len(all_events))


def get_approvals_of_owner(w3: Web3, owner_address: str) -> list[AttributeDict]:
    """
    Returns all of the approvals that the given owner approved

    Args:
        w3 (Web3): The web3 API
        owner_address (str): The owner address that approved

    Returns:
        list[AttributeDict]: All of the approvals that the given owner approved
    """
    pass


def get_contract_token_symbol(w3: Web3, contract_address: str) -> str:
    """
    Returns the token's symbol of the given contract address

    Args:
        contract_address (str): The address of the contract

    Returns:
        str: The symbol of the token
    """
    
    abi = [{"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"}]
    
    contract = w3.eth.contract(contract_address, abi=abi)

    token_symbol = contract.functions.symbol().call() 
    return token_symbol
