from fastapi import FastAPI, Query
from utils import get_approvals_data_of_owner, get_web3_api
from typing import Any
from dataclasses import asdict
import asyncio
from asyncio import Task


app = FastAPI()
w3 = get_web3_api()


async def get_approvals_task(address: str) -> list[dict[str, Any]]:
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
async def read_root():
    """
    API root function.
    """

    return {"hello": "world"}


@app.get("/approvals/")
async def get_approvals(addresses: list[str] = Query(None)):
    """
    Get all approvals of a given list of addresses

    Usage Example:
        http://127.0.0.1:8000/approvals/?addresses=0x005e20fCf757B55D6E27dEA9BA4f90C0B03ef852&addresses=0xE0a2019f2a8784661A25E33753347E67296496e4

    Args:
        addresses (list[str], optional): The list of addresses to query their approvals. Defaults to Query(None).
    """

    tasks_dict: dict[str, Task] = {}
    tasks_list: list[Task] = []
    for address in addresses:
        task = asyncio.create_task(get_approvals_task(address=address))
        tasks_dict[address] = task
        tasks_list.append(task)

    await asyncio.wait(tasks_list)

    return {address: task.result() for address, task in tasks_dict.items()}
