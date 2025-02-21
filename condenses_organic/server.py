from fastapi import FastAPI
from httpx import AsyncClient
from pydantic_settings import BaseSettings
import bittensor as bt
from loguru import logger
from pydantic import BaseModel


class TextCompressProtocol(bt.Synapse):
    context: str = ""
    compressed_context: str = ""


class NodeManagingConfig(BaseModel):
    base_url: str = "http://localhost:9101"


class RestfulBittensorConfig(BaseModel):
    base_url: str = "http://localhost:9103"


class Settings(BaseSettings):
    wallet_name: str = "default"
    wallet_hotkey: str = "default"
    wallet_path: str = "~/.bittensor/wallets"
    node_managing: NodeManagingConfig = NodeManagingConfig()
    restful_bittensor: RestfulBittensorConfig = RestfulBittensorConfig()

    class Config:
        env_file = ".env"


settings = Settings()
logger.info(f"Settings: {settings}")


WALLET = bt.Wallet(
    name=settings.wallet_name,
    hotkey=settings.wallet_hotkey,
    path=settings.wallet_path,
)
DENDRITE = bt.Dendrite(
    wallet=WALLET,
)

app = FastAPI()


class CompressTextRequest(BaseModel):
    text: str
    top_node_performance: float = 0.1


async def get_uid():
    with AsyncClient(base_url=settings.node_managing.base_url) as client:
        response = await client.post("/api/rate-limits/get-uid")
        return response.json()[0]


async def get_axon_info(uid: int):
    with AsyncClient(base_url=settings.restful_bittensor.base_url) as client:
        response = await client.post(
            "/api/metagraph/axons",
            json={"uids": [uid]},
        )
        axon_string = response.json()["axons"][0]
        axon = bt.Axon.from_string(axon_string)
        return axon


@app.post("/api/compress/text")
async def compress_text(request: CompressTextRequest):
    uid = await get_uid()
    axon = await get_axon_info(uid)
    logger.info(f"Text: {request.text[:100]}...")
    logger.info(f"Axon: {axon}")

    response = await DENDRITE.forward(
        axon=axon,
        synapse=TextCompressProtocol(context=request.text),
        timeout=24.0,
    )
    return {
        "compressed_text": response.compressed_context,
    }
