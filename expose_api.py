from fastapi import FastAPI, Query
from utils import get_approvals_data_of_owner, get_web3_api
from typing import Any
from dataclasses import asdict


app = FastAPI()
w3 = get_web3_api()


async def approval_task(address: str) -> list[dict[str, Any]]:
    """
    An approval task, that gets the approvals of the given owner, and formats them as a dict to be returned

    Args:
        address (str): The owner's address to get approvals of

    Returns:
        list[dict[str, Any]]: The list of approvals' data formatted as a dict
    """

    all_approvals_data = get_approvals_data_of_owner(w3=w3, owner_address=address)

    return [asdict(approval_data) for approval_data in all_approvals_data]


@app.get("/")
async def get_approvals(addresses: list[str] = Query(None)):
    """
    Get all approvals of a given list of addresses

    Args:
        addresses (list[str], optional): The list of addresses to query their approvals. Defaults to Query(None).
    """

    # TODO: call the approval_task on each address asynchronously and wait for all answers to be given. Then return them all to the user
