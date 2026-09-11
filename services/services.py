import logging
from datetime import datetime

# from services.broadcast_text import logger
logger = logging.getLogger(__name__)


def get_timestamp() -> str:
    now = datetime.now()
    ts = now.timestamp()
    ts_int = int(ts)
    return str(ts)


def _to_chat_id(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        logger.error("Invalid chat_id: %r", value)
        return None
