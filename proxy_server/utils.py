import time
import bittensor as bt
from datatypes import ValidatorRegisterData, Validator
import logging

logger = logging.getLogger("Utils")


def resync_in_background(metagraph):
    while True:
        logger.info("Resyncing subtensor metagraph")
        metagraph.sync()
        time.sleep(60)
