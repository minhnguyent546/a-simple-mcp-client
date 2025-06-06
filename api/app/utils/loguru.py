from loguru import logger

def init_logger() -> None:
    logger.add(
        'mcp_client.log',
        level='DEBUG',
    )
