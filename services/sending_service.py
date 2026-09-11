import asyncio
import logging

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError, TelegramBadRequest, TelegramAPIError
from aiogram.utils.chat_action import ChatActionSender

from config import bot
# from services.broadcast_text import logger
from services.services import _to_chat_id

logger = logging.getLogger(__name__)


async def send_message_text_to_user(
        uuid: str,
        text: str,
        disable_notification: bool = False,
        max_retries: int = 3,
) -> bool:
    for attempt in range(max_retries):
        try:
            await bot.send_message(
                chat_id=uuid,
                text=text,
                disable_notification=disable_notification,
                parse_mode=ParseMode.HTML,
            )
        except TelegramRetryAfter as e:
            logger.error(
                f"Target [ID:{uuid}]: Flood limit exceeded. "
                f"Sleep {e.retry_after}s (attempt {attempt + 1}/{max_retries})"
            )
            await asyncio.sleep(e.retry_after)
            continue
        except TelegramForbiddenError:
            logger.info(f"Target [ID:{uuid}]: Bot blocked")
            return False
        except TelegramBadRequest as e:
            logger.warning(f"Target [ID:{uuid}]: Bad request: {e}")
            return False
        except TelegramAPIError as e:
            logger.error(f"Target [ID:{uuid}]: Telegram API error: {e}")
            return False
        else:
            logger.info(f"Target [ID:{uuid}]: success")
            return True

    logger.error(f"Target [ID:{uuid}]: failed after {max_retries} attempts")
    return False


async def broadcast_text_all_users(bot: Bot, recipients: list[str], text: str) -> tuple[int, int]:
    ok = failed = 0
    for raw_id in recipients:
        chat_id = _to_chat_id(raw_id)
        if chat_id is None:
            failed += 1
            continue

        try:
            async with ChatActionSender.typing(bot=bot, chat_id=chat_id):
                await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    disable_notification=True,
                    # parse_mode=ParseMode.HTML,
                    parse_mode="HTML",
                )
        except TelegramRetryAfter as e:
            logger.warning("Flood limit, sleep %s", e.retry_after)
            await asyncio.sleep(e.retry_after)
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    disable_notification=True,
                )
                ok += 1
            except TelegramAPIError as err:
                logger.error("Retry failed for %s: %s", chat_id, err)
                failed += 1
            continue
        except TelegramForbiddenError:
            logger.info("Bot blocked by %s", chat_id)
            failed += 1
        except TelegramBadRequest as e:
            logger.warning("Bad request for %s: %s", chat_id, e)
            failed += 1
        except TelegramAPIError as e:
            logger.error("API error for %s: %s", chat_id, e)
            failed += 1
        else:
            ok += 1

        await asyncio.sleep(0.05)  # антифлуд

    return ok, failed
