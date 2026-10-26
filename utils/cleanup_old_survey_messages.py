import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

from config import bot
from core.config import settings
from core.storage import AppStorage
from services.sending_service import LAST_BROADCAST_MSG_ID
from services.services import _to_chat_id

logger = logging.getLogger(__name__)


async def cleanup_old_survey_messages(recipients: list[str] | None = None) -> None:
    """
    Удаляет вчерашние висящие сообщения с опросом у получателей.
    Использует FSM state (Redis) — ключ LAST_BROADCAST_MSG_ID.
    """
    if not AppStorage.is_ready():
        logger.error("cleanup_old_survey_messages: AppStorage не инициализирован")
        return

    target = recipients if recipients is not None else settings.TEST_USERS
    if not target:
        logger.warning("cleanup_old_survey_messages: нет получателей")
        return

    for raw_id in target:
        chat_id = _to_chat_id(raw_id)
        if chat_id is None:
            logger.warning("cleanup: невалидный chat_id для %r", raw_id)
            continue

        try:
            storage_key = StorageKey(
                bot_id=bot.id,
                chat_id=chat_id,
                user_id=chat_id,
                destiny="default",
            )
            user_state = FSMContext(storage=AppStorage.storage, key=storage_key)

            data = await user_state.get_data()
            old_message_id = data.get(LAST_BROADCAST_MSG_ID)

            if not old_message_id:
                continue

            try:
                await bot.delete_message(chat_id=chat_id, message_id=old_message_id)
                logger.info("cleanup: удалено сообщение %s у %s", old_message_id, chat_id)
            except TelegramBadRequest as e:
                logger.info("cleanup: не удалось удалить %s у %s: %s", old_message_id, chat_id, e)
            except TelegramForbiddenError:
                logger.info("cleanup: бот заблокирован у %s", chat_id)

            # Убираем ключ из Redis (pop, а не None)
            data.pop(LAST_BROADCAST_MSG_ID, None)
            await user_state.set_data(data)

        except Exception as e:
            logger.warning("cleanup: ошибка для %s: %s", chat_id, e, exc_info=True)

