from fastapi import FastAPI, Request, Depends
from fastapi.exceptions import HTTPException
from datatypes import (
    RegisterPayload,
    OrganicPayload,
    ValidatorRegisterData,
)
from dependencies import check_authentication
import pymongo
import os
import bittensor as bt
from concurrent.futures import ThreadPoolExecutor
from utils import resync_in_background
import random
import httpx
import time


class ValidatorApp:
    def __init__(self):
        """
        Initialize the ValidatorApp with necessary configurations, database connections, and background tasks.
        """
        print("Initializing ValidatorApp")

        # Read environment variables
        self.NETUID = os.getenv("NETUID", 52)
        self.MONGOHOST = os.getenv("MONGOHOST", "localhost")
        self.MONGOPORT = int(os.getenv("MONGOPORT", 27017))
        self.MONGOUSER = os.getenv("MONGOUSER", "root")
        self.MONGOPASSWORD = os.getenv("MONGOPASSWORD", "example")
        self.SUBTENSOR_NETWORK = os.getenv("SUBTENSOR_NETWORK", "finney")

        # Initialize MongoDB connection
        try:
            self.client = pymongo.MongoClient(
                f"mongodb://{self.MONGOUSER}:{self.MONGOPASSWORD}@{self.MONGOHOST}:{self.MONGOPORT}"
            )
            self.DB = self.client["ncs-client"]
            print(f"Connected to MongoDB at {self.MONGOHOST}:{self.MONGOPORT}")
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise

        # Initialize Subtensor
        try:
            self.subtensor = bt.subtensor(network=self.SUBTENSOR_NETWORK)
            print(f"Connected to Subtensor network {self.SUBTENSOR_NETWORK}")
        except Exception as e:
            print(f"Failed to initialize Subtensor: {e}")
            raise

        # Initialize in-memory validators list and a lock for thread safety
        self.in_memory_validators = []
        self.validators = []

        # Start background tasks
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.executor.submit(resync_in_background, self.subtensor)
        self.executor.submit(self.update_validators_periodically)

        # Initialize FastAPI app
        self.app = FastAPI()

        # Register API endpoints
        self.register_endpoints()

    def update_validators_periodically(self):
        """
        Periodically update the in-memory validators list by checking their availability.
        This function runs in a background thread and updates the list every 15 minutes.
        """
        while True:
            try:
                print("Updating in-memory validators list")
                validators = list(self.DB["validators"].find())
                updated_validators = []

                async def check_validator(validator):
                    endpoint = validator.get("endpoint")
                    if not endpoint:
                        return None
                    try:
                        async with httpx.AsyncClient() as client:
                            response = await client.get(endpoint + "/health")
                            if response.status_code == 200:
                                return validator
                    except httpx.RequestError as e:
                        print(f"Validator at {endpoint} is unreachable: {e}")
                    return None

                # Use asyncio event loop for concurrent HTTP requests
                import asyncio

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                tasks = [check_validator(validator) for validator in validators]
                results = loop.run_until_complete(asyncio.gather(*tasks))
                loop.close()

                # Filter out None results and update in-memory validators
                updated_validators = [v for v in results if v is not None]

                self.in_memory_validators = updated_validators

                print(
                    f"Updated in-memory validators list with {len(self.in_memory_validators)} validators"
                )
            except Exception as e:
                print(f"Error during validators update: {e}")

            # Sleep for 15 minutes before the next update
            time.sleep(900)

    def register_endpoints(self):
        """
        Register the API endpoints with the FastAPI app.
        """

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
                ss58_address, ip_address = client_data
                endpoint = f"http://{ip_address}:{payload.port}"
                data = ValidatorRegisterData(
                    ss58_address=ss58_address,
                    ip_address=ip_address,
                    port=payload.port,
                    endpoint=endpoint,
                    _id=ss58_address,
                )
                result = collection.update_one(
                    {"_id": ss58_address}, {"$set": data.model_dump()}, upsert=True
                )
                print(f"Registered validator {ss58_address} at port {payload.port}")
                print(f"Updated {result.modified_count} documents")

                # Update in-memory validators immediately after registration
                self.in_memory_validators.append(data.model_dump())

                return {"status": "success"}
            except pymongo.errors.PyMongoError as e:
                print(f"Database error during registration: {e}")
                raise HTTPException(status_code=500, detail="Database Error")
            except Exception as e:
                print(f"Unexpected error during registration: {e}")
                raise HTTPException(status_code=500, detail="Internal Server Error")

        @self.app.post("/api/organic")
        async def organic(payload: OrganicPayload):
            """
            Handle organic requests and forward them to a selected validator.

            Parameters:
                payload (OrganicPayload): The payload containing the organic request data.

            Returns:
                dict: The response from the forwarded request.
            """
            try:
                print(f"Received organic request with context {payload.context}")

                validators = self.in_memory_validators.copy()

                if not validators:
                    print("No validators available in the in-memory list")
                    raise HTTPException(
                        status_code=503, detail="No validators available"
                    )

                stakes = []
                urls = []
                for validator in validators:
                    stake = validator.get("stake", 1)
                    endpoint = validator.get("endpoint")
                    if not endpoint:
                        continue  # Skip if endpoint is not available
                    stakes.append(stake)
                    urls.append(endpoint)

                if not urls:
                    print("No valid validator endpoints available")
                    raise HTTPException(
                        status_code=503, detail="No valid validator endpoints available"
                    )

                selected_url = random.choices(urls, weights=stakes, k=1)[0]
                print(f"Selected {selected_url} for forwarding the request")

                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        selected_url + "/forward", json=payload.model_dump()
                    )
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPError as e:
                print(f"HTTP error during forwarding: {e}")
                raise HTTPException(status_code=502, detail="Bad Gateway")
            except Exception as e:
                print(f"Unexpected error during organic request handling: {e}")
                raise HTTPException(status_code=500, detail="Internal Server Error")

    # Additional methods and utilities can be added here if necessary


# Instantiate the ValidatorApp and get the FastAPI app
validator_app = ValidatorApp()
app = validator_app.app

if __name__ == "__main__":
    # Start the FastAPI app
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
