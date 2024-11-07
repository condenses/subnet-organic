from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
import bittensor as bt


def check_authentication(request: Request):
    message = request.headers.get("message")
    ss58_address = request.headers.get("ss58_address")
    signature = request.headers.get("signature")
    keypair = bt.Keypair(ss58_address=ss58_address)
    print(f"Checking authentication for {ss58_address}")
    if not keypair.verify(message, signature):
        raise HTTPException(status_code=401, detail="Invalid token")
    print(f"Authenticated {ss58_address}")
    ip_address = request.headers.get("X-Real-Ip") or request.client.host

    return ss58_address, ip_address, message
