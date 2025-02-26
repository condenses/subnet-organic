from fastapi import FastAPI, HTTPException, Depends, Header
from httpx import AsyncClient
from pydantic_settings import BaseSettings
import bittensor as bt
from loguru import logger
from pydantic import BaseModel
from .taostats_api import TaostatsAPI
import asyncio
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


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
    api_key: str = None  # API key for accessing this service

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


class CompressMessagesRequest(BaseModel):
    messages: list[dict]  # List of message objects with 'role' and 'content' fields
    compress_user: bool = True
    compress_assistant: bool = True
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


security = HTTPBearer()


async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify the API key from Authorization header."""
    if settings.api_key is None:
        # If no API key is set, allow all requests
        return True

    if credentials.credentials != settings.api_key:
        logger.warning(f"Invalid API key provided")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True


@app.post("/api/compress/text")
async def compress_text(
    request: CompressTextRequest, authorized: bool = Depends(verify_api_key)
):
    try:
        logger.info("Starting text compression request")
        uid = await get_uid(request.top_node_performance)
        logger.info(f"Using UID: {uid}")

        axon = await get_axon_info(uid)
        logger.info(f"Text: {request.text[:100]}...")
        logger.info(f"Axon: {axon}")

        logger.debug("Sending compression request to dendrite")
        compressed_text = await compress_with_retries(axon, request.text)
        return {
            "compressed_text": compressed_text,
        }
    except Exception as e:
        logger.error(f"Error during text compression: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/compress/messages")
async def compress_messages(
    request: CompressMessagesRequest, authorized: bool = Depends(verify_api_key)
):
    try:
        logger.info("Starting messages compression request")
        uid = await get_uid(request.top_node_performance)
        logger.info(f"Using UID: {uid}")

        axon = await get_axon_info(uid)
        logger.debug(f"Processing {len(request.messages)} messages")

        # Filter messages that need compression
        messages_to_compress = []
        message_indices = []

        for i, message in enumerate(request.messages):
            role = message.get("role", "")
            content = message.get("content", "")

            # Skip system messages or messages with roles we don't want to compress
            if role == "system":
                continue

            if (role == "user" and not request.compress_user) or (
                role == "assistant" and not request.compress_assistant
            ):
                continue

            messages_to_compress.append(content)
            message_indices.append(i)

        # Compress messages in parallel with retries
        compression_tasks = []
        for content in messages_to_compress:
            task = compress_with_retries(axon, content)
            compression_tasks.append(task)

        # Wait for all compression tasks to complete
        if compression_tasks:
            compression_results = await asyncio.gather(*compression_tasks)
        else:
            compression_results = []

        # Create the result with compressed messages
        compressed_messages = request.messages.copy()
        for idx, result in zip(message_indices, compression_results):
            compressed_messages[idx]["content"] = result

        logger.info(f"Compressed {len(messages_to_compress)} messages in parallel")
        return {
            "compressed_messages": compressed_messages,
        }
    except Exception as e:
        logger.error(f"Error during messages compression: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def compress_with_retries(axon, content, max_retries=3):
    """Attempt to compress content with retries, keeping original if all attempts fail."""
    for attempt in range(max_retries):
        try:
            response = await DENDRITE.forward(
                axons=axon,
                synapse=TextCompressProtocol(context=content),
                timeout=24.0,
            )
            logger.info(
                f"Got compressed response of length: {len(response.compressed_context)}"
            )
            return response.compressed_context
        except Exception as e:
            logger.warning(f"Compression attempt {attempt+1}/{max_retries} failed: {e}")
            if attempt == max_retries - 1:
                logger.warning(
                    f"All compression attempts failed, keeping original content"
                )
                return content
            # Wait a bit before retrying
            await asyncio.sleep(0.05)
