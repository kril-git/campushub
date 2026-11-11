import logging
import re
from datetime import datetime

# from services.broadcast_text import logger
logger = logging.getLogger(__name__)

# Регулярка для даты: YYYY-MM-DD HH:MM
DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")


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


def _is_date(text: str) -> bool:
    return bool(DATE_REGEX.match(text.strip()))