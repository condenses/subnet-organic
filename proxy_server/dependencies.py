from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
import bittensor as bt
import time


def check_authentication(request: Request):
    message = request.headers.get("message")
    ss58_address = request.headers.get("ss58_address")
    signature = request.headers.get("signature")
    authentication_key, nonce = message.split(":")
    latency = time.time_ns() - int(nonce)
    print(f"Latency: {latency}")
    if latency / 1e9 > 48:
        raise HTTPException(
            status_code=401, detail=f"Invalid nonce, too old: {latency / 1e9}"
        )
    keypair = bt.Keypair(ss58_address=ss58_address)
    print(f"Checking authentication for {ss58_address}")
    if not keypair.verify(message, signature):
        raise HTTPException(status_code=401, detail="Invalid token")
    print(f"Authenticated {ss58_address}")
    ip_address = request.headers.get("X-Real-Ip") or request.client.host

    return ss58_address, ip_address, authentication_key
