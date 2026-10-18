import asyncio
import logging

from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import readonly
from database.users_crud import get_user_by_uuid
from lexicon.lexicon import LEXICON_USER_HELP
from models import User
from services.pool_service import PoolService
from utils.converters import uuid_to_str
from database.dao.users_dao import UserDAO

logger = logging.getLogger(__name__)


class UserService:
    @staticmethod
    @readonly
    async def is_registered_user(session: AsyncSession, uuid: str | int) -> bool:
        uuid_str = await uuid_to_str(uuid=uuid)
        return await UserDAO.is_registered(session=session, uuid=uuid_str)


# рабочий
async def get_help_user(message: Message) -> dict:
    """ Пока бот говорит только по-русски """
    locale = message.from_user.language_code
    if locale is None or "":
        locale = "ru"
    locale = "ru"
    from lexicon.lexicon import LEXICON_USER_HELP
    data = LEXICON_USER_HELP[locale.upper()].copy()
    user: User = await get_user_by_uuid(uuid=message.from_user.id)  # type: ignore
    if not user.registration:
        data.update({"registration": "Пройти регистрацию"})
    active_pool = await PoolService.get_active_pool_id()
    completed: bool = await PoolService.check_survey_completion(
        pool_id=active_pool, user_uuid=str(message.from_user.id)
    )
    await message.answer(f"active_pool {active_pool}   completed {completed}")

    if active_pool is not None and not completed:
        await message.answer(f"Активный опрос {active_pool}")
        data.update({"complete_a_survey": "Пройти текущий опрос"})
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
