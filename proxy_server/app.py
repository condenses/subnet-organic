from fastapi import FastAPI, Request, Depends, Header
from fastapi.exceptions import HTTPException
from datatypes import RegisterPayload, OrganicPayload, ValidatorRegisterData
from dependencies import check_authentication
import pymongo
import os
import bittensor as bt
from concurrent.futures import ThreadPoolExecutor
from utils import resync_in_background
import random
import httpx
import asyncio
from logging import getLogger, basicConfig

# Setup logging
basicConfig(level="INFO")
logger = getLogger(__name__)


class ValidatorApp:
    def __init__(self):
        """
        Initialize the ValidatorApp with necessary configurations, database connections, and background tasks.
        """
        logger.info("Initializing ValidatorApp")

        # Read environment variables
        self.NETUID = int(os.getenv("NETUID", 52))
        self.MONGOHOST = os.getenv("MONGOHOST", "localhost")
        self.MONGOPORT = int(os.getenv("MONGOPORT", 27017))
        self.MONGOUSER = os.getenv("MONGOUSER", "root")
        self.MONGOPASSWORD = os.getenv("MONGOPASSWORD", "example")
        self.SUBTENSOR_NETWORK = os.getenv("SUBTENSOR_NETWORK", "finney")
        self.ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
        self.MIN_STAKE = int(os.getenv("MIN_STAKE", 1000))

        # Initialize MongoDB connection
        self.client = None
        self.DB = None
        self.initialize_mongo_connection()

        # Initialize Subtensor
        self.subtensor = None
        self.metagraph = None
        self.initialize_subtensor()

        # Initialize in-memory validators list and a lock for thread safety
        self.in_memory_validators = {}
        self.lock = asyncio.Lock()

        # Start background tasks
        self.background_tasks = []
        self.start_background_tasks()

        # Initialize FastAPI app
        self.app = FastAPI()

        # Register API endpoints
        self.register_endpoints()

    def initialize_mongo_connection(self):
        try:
            self.client = pymongo.MongoClient(
                f"mongodb://{self.MONGOUSER}:{self.MONGOPASSWORD}@{self.MONGOHOST}:{self.MONGOPORT}",
                serverSelectionTimeoutMS=5000,
            )
            self.client.admin.command("ping")  # Test connection
            self.DB = self.client["ncs-client"]
            logger.info(f"Connected to MongoDB at {self.MONGOHOST}:{self.MONGOPORT}")
        except pymongo.errors.PyMongoError as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def initialize_subtensor(self):
        try:
            self.subtensor = bt.subtensor(network=self.SUBTENSOR_NETWORK)
            self.metagraph = self.subtensor.metagraph(self.NETUID)
            logger.info(f"Connected to Subtensor network {self.SUBTENSOR_NETWORK}")
        except Exception as e:
            logger.error(f"Failed to initialize Subtensor: {e}")
            raise

    def start_background_tasks(self):
        # Start background tasks safely
        loop = asyncio.get_event_loop()
        self.background_tasks.append(
            loop.create_task(resync_in_background(self.metagraph))
        )
        self.background_tasks.append(
            loop.create_task(self.update_validators_periodically())
        )

    async def update_validators_periodically(self):
        while True:
            try:
                await self.update_validators()
            except Exception as e:
                logger.error(f"Error during validators update: {e}")
            await asyncio.sleep(900)  # Sleep for 15 minutes

    async def update_validators(self):
        async with self.lock:
            logger.info("Updating in-memory validators list")
            validators = list(self.DB["validators"].find())
            updated_validators = []

            async def check_validator(validator):
                endpoint = validator.get("endpoint")
                if not endpoint:
                    return None
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(endpoint + "/health", timeout=4)
                        if response.status_code == 200:
                            return validator
                except httpx.RequestError as e:
                    logger.warning(f"Validator at {endpoint} is unreachable: {e}")
                return None

            tasks = [check_validator(validator) for validator in validators]
            results = await asyncio.gather(*tasks)
            updated_validators = {v["_id"]: v for v in results if v}

            self.in_memory_validators = updated_validators
            logger.info(
                f"Updated in-memory validators list with {len(self.in_memory_validators)} validators"
            )

    def register_endpoints(self):
        """
        Register the API endpoints with the FastAPI app.
        """

        @self.app.post("/api/user-register")
        async def register_user(
            request: Request,
            admin_api_key: str = Header(...),
        ):
            """
            Register a new user API key, authenticated by the admin API key.
            """
            if admin_api_key != self.ADMIN_API_KEY:
                raise HTTPException(status_code=403, detail="Unauthorized")

            payload = await request.json()
            user_api_key = payload.get("api_key")

            if not user_api_key:
                raise HTTPException(status_code=400, detail="API key required")

            try:
                self.DB["users"].insert_one({"api_key": user_api_key})
                return {"status": "success", "message": "User API key registered"}
            except pymongo.errors.DuplicateKeyError:
                raise HTTPException(status_code=400, detail="API key already exists")
            except pymongo.errors.PyMongoError as e:
                logger.error(f"Database error during API key registration: {e}")
                raise HTTPException(status_code=500, detail="Database Error")

        @self.app.post("/register")
        async def register(
            request: Request,
        ):
            """
            Register a validator with the provided payload and client data.
            """
            client_data = check_authentication(request)
            payload = RegisterPayload(**await request.json())
            try:
                collection = self.DB["validators"]
                ss58_address, ip_address, message = client_data
                endpoint = f"http://{ip_address}:{payload.port}"
                data = ValidatorRegisterData(
                    ss58_address=ss58_address,
                    ip_address=ip_address,
                    port=payload.port,
                    endpoint=endpoint,
                    _id=ss58_address,
                    message=message,
                )

                result = collection.delete_many({"endpoint": endpoint})
                logger.info(
                    f"Deleted {result.deleted_count} documents with the same endpoint: {endpoint}"
                )

                result = collection.update_one(
                    {"_id": ss58_address}, {"$set": data.model_dump()}, upsert=True
                )
                logger.info(
                    f"Registered validator {ss58_address} at port {payload.port}"
                )
                await self.update_validators()
                self.in_memory_validators[ss58_address] = data.model_dump()
                return {"status": "success"}
            except pymongo.errors.PyMongoError as e:
                logger.error(f"Database error during registration: {e}")
                raise HTTPException(status_code=500, detail="Database Error")
            except Exception as e:
                logger.error(f"Unexpected error during registration: {e}")
                raise HTTPException(status_code=500, detail="Internal Server Error")

        @self.app.post("/api/organic")
        async def organic(payload: OrganicPayload, user_api_key: str = Header(...)):
            """
            Handle organic requests, authenticate with user API key, and forward to a selected validator.
            """
            user = self.DB["users"].find_one({"api_key": user_api_key})
            if not user:
                raise HTTPException(status_code=403, detail="Unauthorized")

            try:
                validators = self.in_memory_validators.copy()
                if not validators:
                    raise HTTPException(
                        status_code=503, detail=f"No validators available: {validators}"
                    )

                stakes = []
                ss58_addresses = []
                for validator in validators.values():
                    try:
                        ss58_address = validator.get("ss58_address")
                        uid = self.metagraph.hotkeys.index(ss58_address)
                        stake = self.metagraph.total_stake[uid]
                        if stake < self.MIN_STAKE:
                            continue
                        stakes.append(stake)
                        ss58_addresses.append(ss58_address)
                    except ValueError:
                        logger.warning(
                            f"Validator {ss58_address} not found in metagraph"
                        )

                if not stakes:
                    raise HTTPException(
                        status_code=503, detail="No valid validator endpoints available"
                    )

                hotkey = random.choices(ss58_addresses, weights=stakes, k=1)[0]
                selected_url = validators[hotkey].get("endpoint")
                message = validators[hotkey].get("message")

                async with httpx.AsyncClient(timeout=32) as client:
                    response = await client.post(
                        selected_url + "/forward",
                        json=payload.model_dump(),
                        headers={"message": message},
                    )
                    if response.status_code != 200:
                        raise HTTPException(
                            status_code=response.status_code, detail=response.text
                        )
                    return response.json()
            except httpx.RequestError as e:
                logger.error(f"Error during organic request forwarding: {e}")
                raise HTTPException(status_code=503, detail="Forwarding Error")

    def shutdown(self):
        """
        Cleanup resources on app shutdown.
        """
        if self.client:
            self.client.close()
        for task in self.background_tasks:
            task.cancel()


# Instantiate the ValidatorApp and get the FastAPI


# Instantiate the ValidatorApp and get the FastAPI app
validator_app = ValidatorApp()
app = validator_app.app

if __name__ == "__main__":
    # Start the FastAPI app
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
