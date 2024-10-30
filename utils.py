import time
import bittensor as bt
from datatypes import ValidatorRegisterData, Validator
import logging

logger = logging.getLogger("Utils")


def resync_in_background(subtensor: bt.Subtensor):
    while True:
        logger.info("Resyncing subtensor metagraph")
        subtensor.metagraph.sync()
        time.sleep(60)
