import httpx
import asyncio
from pydantic import BaseModel
import bittensor as bt
from loguru import logger


class AxonInfo(BaseModel):
    block: int
    ip: str
    ipType: int
    placeholder1: int
    placeholder2: int
    port: int
    protocol: int
    version: int


class Node(BaseModel):
    hotkey: dict
    coldkey: dict
    netuid: int
    uid: int
    block_number: int
    timestamp: str
    stake: str
    trust: str
    validator_trust: str
    consensus: str
    incentive: str
    dividends: str
    emission: str
    active: bool
    validator_permit: bool
    updated: int
    daily_reward: str
    registered_at_block: int
    is_immunity_period: bool
    rank: int
    is_child_key: bool
    axon: AxonInfo | None

    def get_axon_info(self) -> bt.AxonInfo:
        if self.axon is None:
            raise ValueError("Axon info not found")
        return bt.AxonInfo(
            version=self.axon.version,
            ip=self.axon.ip,
            port=self.axon.port,
            ip_type=self.axon.ipType,
            hotkey=self.hotkey["ss58"],
            coldkey=self.coldkey["ss58"],
        )


class Metagraph(BaseModel):
    nodes: dict[int, Node]


class TaostatsAPI:
    def __init__(self, subnet_id: int, sync_interval: int = 300, api_key: str = None):
        if api_key is None:
            logger.error("TAOSTATS_API_KEY is required")
            raise ValueError("TAOSTATS_API_KEY is required")
        self.api_key = api_key
        self.subnet_id = subnet_id
        self.sync_interval = sync_interval
        self.base_url = "https://api.taostats.io/api"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": self.api_key,
        }
        self.nodes = {}

    async def periodically_sync_nodes(self):
        while True:
            await self.sync_nodes()
            await asyncio.sleep(self.sync_interval)

    async def sync_nodes(self):
        logger.info("Syncing nodes")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/metagraph/latest/v1?netuid=47&limit=256",
                    headers=self.headers,
                    timeout=32,
                )
                response.raise_for_status()
                data = response.json()
                nodes = [Node(**node_data) for node_data in data["data"]]
                self.nodes = {node.uid: node for node in nodes}
        except Exception as e:
            logger.error(f"Error syncing nodes: {e}")

    async def get_node_by_uid(self, uid: int) -> Node | None:
        return self.nodes.get(uid)
