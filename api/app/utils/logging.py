import logging
import sys


logger = logging.getLogger('mcp_client')
logger.setLevel(logging.DEBUG)

def init_logger(log_level=logging.INFO) -> logging.Logger:
    logger = logging.getLogger('mcp_client')
    logger.setLevel(log_level)

    # set file handler
    file_handler = logging.FileHandler('mcp_client.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '[%(asctime)s - %(name)s] %(levelname)s - %(message)s'
    ))
    logger.addHandler(file_handler)

    # set stream handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        '[%(asctime)s - %(name)s] %(levelname)s - %(message)s'
    ))
    logger.addHandler(console_handler)

    return logger
