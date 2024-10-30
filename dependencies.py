from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
import bittensor as bt


async def check_authentication(
    subtensor: bt.Subtensor, netuid: int, request: Request, call_next
):
    message = request.headers.get("message")
    ss58_address = request.headers.get("ss58_address")
    signature = request.headers.get("signature")
    keypair = bt.Keypair(ss58_address=ss58_address)

    if not keypair.verify(message, signature):
        raise HTTPException(status_code=401, detail="Invalid token")

    ip_address = request.client.host

    return ss58_address, ip_address
