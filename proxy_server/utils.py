import asyncio
import logging

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
            await asyncio.to_thread(metagraph.sync)  # Run the sync operation in a thread
            logger.info("Metagraph resync completed.")
        except Exception as e:
            logger.error(f"Error during metagraph resync: {e}")
        await asyncio.sleep(60)  # Wait for 60 seconds before the next sync
