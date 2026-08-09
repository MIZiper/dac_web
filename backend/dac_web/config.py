import logging
import os
import sys

DEBUG = os.getenv("DEBUG", "").lower() in ("1", "true", "yes")


def setup_logging():
    logger = logging.getLogger("dac_web")
    if DEBUG:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        ))
        logger.addHandler(handler)
    else:
        logger.setLevel(logging.WARNING)
    logger.debug("DEBUG mode enabled")
