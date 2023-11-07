import logging
import os
import sys

from common.configs import LOG_LEVEL

FORMAT = '%(asctime)s  %(name)s:%(lineno)s -> (%(levelname)s)  %(message)s'

logging.getLogger("urllib3").setLevel(logging.INFO)


def module_logger(n=__name__):
    formatter = logging.Formatter(FORMAT)
    logger = logging.getLogger(n)
    logger.setLevel(LOG_LEVEL)
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setLevel(LOG_LEVEL)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.propagate = 0
    return logger
