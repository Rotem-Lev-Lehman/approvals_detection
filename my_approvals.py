import argparse
from web3 import Web3
from utils import print_approvals_of_owner

parser = argparse.ArgumentParser(
    description="Get all approvals for an address on the blockchain."
)
parser.add_argument(
    "--address",
    type=str,
    required=True,
    help="The address on the blockchain to get approvals of.",
)

args = parser.parse_args()
address: str = args.address

mainnet_url = "mainnet.infura.io/v3"
with open("api_key.txt", "r") as key_file:
    api_key = key_file.read()

provider_url = f"{mainnet_url}/{api_key}"
w3 = Web3(Web3.HTTPProvider(f"https://{provider_url}"))

print_approvals_of_owner(w3=w3, owner_address=address)
