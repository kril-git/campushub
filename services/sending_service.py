import asyncio
import logging

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError, TelegramBadRequest, TelegramAPIError
from aiogram.fsm import storage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply
from aiogram.utils.chat_action import ChatActionSender

from config import bot
from core.config import settings
# from core.dependencies import AppDependencies
from services.services import _to_chat_id

logger = logging.getLogger(__name__)

LAST_BROADCAST_MSG_ID = "last_broadcast_msg_id"


async def send_message_io_and_mio_moglie():
    user_id = settings.TEST_USERS
    for id in user_id:
        await send_message_text_to_user(uuid=id, text="Доброе утро!")


async def send_message_text_to_user(
        uuid: str,
        text: str,
        disable_notification: bool = False,
        reply_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | ReplyKeyboardRemove | ForceReply | None = None,
        max_retries: int = 3,
) -> bool:
    for attempt in range(max_retries):
        try:
            await bot.send_message(
                chat_id=uuid,
                text=text,
                disable_notification=disable_notification,
                reply_markup=reply_markup,
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


async def broadcast_text_all_users(bot: Bot,
                                   recipients: list[str],
                                   text: str,
                                   reply_markup: (
                                           InlineKeyboardMarkup |
                                           ReplyKeyboardMarkup |
                                           ReplyKeyboardRemove |
                                           ForceReply |
                                           None
                                   ) = None,
                                   save_last_message: bool = False, ) -> tuple[int, int]:
    ok = failed = 0
    for raw_id in recipients:
        chat_id = _to_chat_id(raw_id)
        if chat_id is None:
            failed += 1
            continue
        sent_message = None
        try:
            async with ChatActionSender.typing(bot=bot, chat_id=chat_id):
                sent_message = await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    disable_notification=True,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML,
                    # parse_mode="HTML",
                )
        except TelegramRetryAfter as e:
            logger.warning("Flood limit, sleep %s", e.retry_after)
            await asyncio.sleep(e.retry_after)
            try:
                sent_message = await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=reply_markup,
                    disable_notification=True,
                )
                ok += 1
            except TelegramAPIError as err:
                logger.error("Retry failed for %s: %s", chat_id, err)
                failed += 1
            continue
        # except TelegramForbiddenError:
        #     logger.info("Bot blocked by %s", chat_id)
        #     failed += 1
        # except TelegramBadRequest as e:
        #     logger.warning("Bad request for %s: %s", chat_id, e)
        #     failed += 1
        # except TelegramAPIError as e:
        #     logger.error("API error for %s: %s", chat_id, e)
        #     failed += 1
        # else:
        #     ok += 1
        except (TelegramForbiddenError, TelegramBadRequest, TelegramAPIError) as e:
            logger.error("Error sending to %s: %s", chat_id, e)
            failed += 1
            continue

            # Если сообщение успешно ушло пользователю
        if sent_message:
            ok += 1
            if save_last_message:
                try:
                    from core.dependencies import AppDependencies
                    actual_storage = AppDependencies.storage

                    storage_key = StorageKey(bot_id=bot.id, chat_id=chat_id, user_id=chat_id, destiny="default")
                    user_state = FSMContext(storage=actual_storage, key=storage_key)
                    current_data = await user_state.get_data()
                    current_data[LAST_BROADCAST_MSG_ID] = sent_message.message_id
                    await user_state.set_data(current_data)
                except Exception as ex:
                    logger.error(f"Ошибка сохранения message_id для {chat_id}: {ex}")
        await asyncio.sleep(0.05)  # антифлуд

    return ok, failed
