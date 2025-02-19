import asyncio
import logging
import random

logger = logging.getLogger("Utils")

async def resync_in_background(metagraph):
    """
    Periodically resync the subtensor metagraph in the background.
    
    Args:
        metagraph: The metagraph instance to sync.
    """
    while True:
        try:
            logger.info("Resyncing subtensor metagraph...")
            sync_success = False
            retry_count = 0
            max_retries = 100

            while not sync_success and retry_count < max_retries:
                try:
                    await asyncio.to_thread(metagraph.sync)  # Run the sync operation in a thread
                    sync_success = True
                except Exception as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        logger.error(f"Failed to sync metagraph after {max_retries} attempts: {e}")
                        raise  # Re-raise the exception to be caught outside the loop
                    sleep_time = random.uniform(3, 5)
                    await asyncio.sleep(sleep_time)

            logger.info("Metagraph resync completed.")
        except Exception as e:
            logger.error(f"Error during metagraph resync: {e}")
        await asyncio.sleep(600)  # Wait for 600 seconds before the next sync
