from fastapi import FastAPI, HTTPException
from httpx import AsyncClient
from pydantic_settings import BaseSettings
import bittensor as bt
from loguru import logger
from pydantic import BaseModel
from .taostats_api import TaostatsAPI
import asyncio


class TextCompressProtocol(bt.Synapse):
    context: str = ""
    compressed_context: str = ""


class NodeManagingConfig(BaseModel):
    base_url: str = "http://localhost:9101"


class TaostatsConfig(BaseModel):
    subnet_id: int = 47
    sync_interval: int = 300
    api_key: str = None


class Settings(BaseSettings):
    wallet_name: str = "default"
    wallet_hotkey: str = "default"
    wallet_path: str = "~/.bittensor/wallets"
    node_managing: NodeManagingConfig = NodeManagingConfig()
    taostats: TaostatsConfig = TaostatsConfig()

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"


settings = Settings()
logger.info(f"Settings: {settings}")


logger.info(
    f"Creating wallet: {settings.wallet_name} with hotkey: {settings.wallet_hotkey} at path: {settings.wallet_path}"
)
WALLET = bt.Wallet(
    name=settings.wallet_name,
    hotkey=settings.wallet_hotkey,
    path=settings.wallet_path,
)
logger.info(f"Creating dendrite with wallet: {WALLET}")
DENDRITE = bt.Dendrite(
    wallet=WALLET,
)

logger.info(
    f"Creating TAOSTATS API with subnet_id: {settings.taostats.subnet_id} and sync_interval: {settings.taostats.sync_interval}"
)
TAOSTATS_API = TaostatsAPI(
    subnet_id=settings.taostats.subnet_id,
    sync_interval=settings.taostats.sync_interval,
    api_key=settings.taostats.api_key,
)

app = FastAPI()

logger.info(f"Starting app")


@app.on_event("startup")
async def startup_event():
    # Start the periodic sync task as a background task
    asyncio.create_task(TAOSTATS_API.periodically_sync_nodes())


class CompressTextRequest(BaseModel):
    text: str
    top_node_performance: float = 0.1


async def get_uid(top_fraction: float = 0.1):
    logger.debug(f"Getting UID from {settings.node_managing.base_url}")
    async with AsyncClient(
        base_url=settings.node_managing.base_url, timeout=12.0
    ) as client:
        response = await client.post(
            "/api/rate-limits/consume",
            json={"top_fraction": top_fraction},
        )
        data = response.json()
        logger.debug(f"Got data: {data}")
        response.raise_for_status()
        uid = data[0]
        logger.debug(f"Got UID: {uid}")
        return uid


async def get_axon_info(uid: int) -> bt.AxonInfo:
    logger.debug(f"Getting axon info for UID {uid} from TAOSTATS DATA")
    node = await TAOSTATS_API.get_node_by_uid(uid)
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return node.get_axon_info()


@app.post("/api/compress/text")
async def compress_text(request: CompressTextRequest):
    try:
        logger.info("Starting text compression request")
        uid = await get_uid(request.top_node_performance)
        logger.info(f"Using UID: {uid}")

        axon = await get_axon_info(uid)
        logger.info(f"Text: {request.text[:100]}...")
        logger.info(f"Axon: {axon}")

        logger.debug("Sending compression request to dendrite")
        response = await DENDRITE.forward(
            axons=axon,
            synapse=TextCompressProtocol(context=request.text),
            timeout=24.0,
        )
        logger.info(
            f"Got compressed response of length: {len(response.compressed_context)}"
        )
        return {
            "compressed_text": response.compressed_context,
        }
    except Exception as e:
        logger.error(f"Error during text compression: {e}")
        raise HTTPException(status_code=500, detail=str(e))
