import asyncio
import logging

from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError
from aiogram.types import Message

from database.users_crud import get_user_by_uuid
from lexicon.lexicon import LEXICON_USER_HELP
from models import User

logger = logging.getLogger(__name__)


# рабочий
async def get_help_user(message: Message) -> dict:
    """ Пока бот говорит только по-русски """
    locale = message.from_user.language_code
    if locale is None or "":
        locale = "ru"
    locale = "ru"
    from lexicon.lexicon import LEXICON_USER_HELP
    data = LEXICON_USER_HELP[locale.upper()]
    user: User = await get_user_by_uuid(uuid=message.from_user.id)  # type: ignore
    if not user.registration:
        data.update({"/registration": "Пройти регистрацию"})
    return data


async def send_dict(message: Message, data: dict):
    """
    Принимает словарь и отправляет его автору запроса в цикле.
    """
    for key, value in data.items():
        try:
            await message.answer(f"{key} - {value}\n")
        except TelegramRetryAfter as e:
            logger.error(f"Target: Flood limit is exceeded. "
                         f"Sleep {e.retry_after} seconds."
                         )
            await asyncio.sleep(e.retry_after)
            await message.answer(f"{key} - {value}\n")
        # except TelegramForbiddenError:
        #     logger.info(f"Target [ID:{user.uuid}]: Bot Blocked")

    logger.info(f"dict successful sent.")


async def send_list(message: Message, data: list):
    """
    Принимает словарь и отправляет его автору запроса в цикле.
    """
    for item in data:
        try:
            await message.answer(f"{item}\n")
        except TelegramRetryAfter as e:
            logger.error(f"Target: Flood limit is exceeded. "
                         f"Sleep {e.retry_after} seconds."
                         )
            await asyncio.sleep(e.retry_after)
            await message.answer(f"{item}\n")
        except TelegramForbiddenError:
            logger.info(f"Target [ID:{message.from_user.id}]: Bot Blocked")

    logger.info(f"dict successful sent.")


async def create_str_from_dict(data: dict) -> str:
    """
    Принимает словарь, возвращает склеенную строку.
    Хотелось бы добавить контроль ограничения длинны строки в телеграмме 4096 символов.
    """
    result: str = ""
    list_str: list = []
    for key, value in data.items():
        list_str.append(f"{key} - {value}\n")
    return result.join(list_str)
