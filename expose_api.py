from fastapi import FastAPI, Query
from utils import get_approvals_data_of_owner, get_web3_api
from typing import Any
from dataclasses import asdict
import asyncio
from asyncio import Future
from concurrent.futures import ThreadPoolExecutor


app = FastAPI()
w3 = get_web3_api()
_executer = ThreadPoolExecutor(4)


def get_approvals_task(address: str) -> list[dict[str, Any]]:
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

    loop = asyncio.get_event_loop()

    futures_dict: dict[str, Future] = {}
    futures_list: list[Future] = []
    for address in addresses:
        # Use run_in_executer since the functions in web3 are not marked with async,
        # and therefore can't be ran with it just like that (could be blocking).
        future = loop.run_in_executor(_executer, get_approvals_task, address)
        futures_dict[address] = future
        futures_list.append(future)

    await asyncio.wait(futures_list)

    return {address: task.result() for address, task in futures_dict.items()}
