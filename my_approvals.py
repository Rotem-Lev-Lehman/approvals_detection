import argparse
from web3 import Web3
from web3.types import FilterParams
from web3._utils.filters import construct_event_filter_params
from web3._utils.events import get_event_data
import json

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

event = ERC20.events.Approval
codec = w3.codec

data_filter_set, event_filter_params = construct_event_filter_params(
    abi,
    codec,
    CONTINUE HERE
)


# event_filter = w3.eth.filter({"address": address})
w3.eth.get_logs(FilterParams(address=address, topics=))

