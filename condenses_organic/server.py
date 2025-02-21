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
    logger.debug(f"Getting UID from {settings.node_managing.base_url}")
    with AsyncClient(base_url=settings.node_managing.base_url) as client:
        response = await client.post("/api/rate-limits/get-uid")
        uid = response.json()[0]
        logger.debug(f"Got UID: {uid}")
        return uid


async def get_axon_info(uid: int):
    logger.debug(f"Getting axon info for UID {uid} from {settings.restful_bittensor.base_url}")
    with AsyncClient(base_url=settings.restful_bittensor.base_url) as client:
        response = await client.post(
            "/api/metagraph/axons",
            json={"uids": [uid]},
        )
        axon_string = response.json()["axons"][0]
        logger.debug(f"Got axon string: {axon_string}")
        axon = bt.Axon.from_string(axon_string)
        logger.debug(f"Parsed axon: {axon}")
        return axon


@app.post("/api/compress/text")
async def compress_text(request: CompressTextRequest):
    logger.info("Starting text compression request")
    uid = await get_uid()
    logger.info(f"Using UID: {uid}")
    
    axon = await get_axon_info(uid)
    logger.info(f"Text: {request.text[:100]}...")
    logger.info(f"Axon: {axon}")

    logger.debug("Sending compression request to dendrite")
    response = await DENDRITE.forward(
        axon=axon,
        synapse=TextCompressProtocol(context=request.text),
        timeout=24.0,
    )
    logger.info(f"Got compressed response of length: {len(response.compressed_context)}")
    return {
        "compressed_text": response.compressed_context,
    }
