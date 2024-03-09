import argparse
from web3 import Web3
from utils import (
    get_approvals_of_owner_filter,
    get_contract_token_symbol,
    parse_approval_logs,
    APPROVALS_ABI,
)

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
address = int(args.address, base=0)

mainnet_url = "mainnet.infura.io/v3"
with open("api_key.txt", "r") as key_file:
    api_key = key_file.read()

provider_url = f"{mainnet_url}/{api_key}"
w3 = Web3(Web3.HTTPProvider(f"https://{provider_url}"))


approval_contract = w3.eth.contract(abi=APPROVALS_ABI)

approval_event = approval_contract.events.Approval()
codec = w3.codec


approvals_filter = get_approvals_of_owner_filter(
    w3=w3, approval_event=approval_event, codec=codec, owner_address=address
)
logs = approvals_filter.get_all_entries()
approval_events = parse_approval_logs(
    approval_event=approval_event, codec=codec, logs=logs
)
for approval in approval_events:
    token_symbol = get_contract_token_symbol(w3=w3, contract_address=approval.address)
    print(token_symbol)
