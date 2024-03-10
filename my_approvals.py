import argparse
from utils import print_approvals_of_owner, get_web3_api

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

w3 = get_web3_api()

print_approvals_of_owner(w3=w3, owner_address=address)
