import asyncio
import logging

from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError
from aiogram.types import Message

from config import settings
# from models import User, UserPool
from models import User
from typing import Callable, Iterable, TypeVar

logger = logging.getLogger(__name__)


# async def send_admin_help(data: dict, message: Message):
#     pass

async def get_uuid_str(uuid: str | int) -> str:
    if isinstance(uuid, int):
        return str(uuid)
    else:
        return uuid


async def _is_admin(uuid: int | str) -> bool:
    if isinstance(uuid, int):
        if str(uuid) in settings.ADMINS:
            return True
        else:
            return False
    if isinstance(uuid, str):
        if uuid in settings.ADMINS:
            return True
        else:
            return False


# рабочий
async def get_help_admin(message: Message) -> dict:
    """ Пока бот говорит только по-русски """
    locale = message.from_user.language_code
    if locale is None or "":
        locale = "ru"
    locale = "ru"
    from lexicon.lexicon import LEXICON_ADMIN_HELP
    data = LEXICON_ADMIN_HELP[locale.upper()]
    return data


async def get(message: Message, content: str) -> dict:
    if message.from_user.language_code == "ru":
        import lexicon.lexicon_ru as locale
    else:
        import lexicon.lexicon_en as locale
    match content:
        case "LEXICON_ADMIN_HELP":
            return locale.LEXICON_ADMIN_HELP


# async def send_users_list(message: Message, users: list[User]) -> int:
#     count: int = 1
#     for user in users:
#         try:
#             await message.answer(f"{count}, {user.uuid}, {user.first_name}, {user.role}\n")
#             count = count + 1
#         except TelegramRetryAfter as e:
#             logger.error(f"Target: Flood limit is exceeded. "
#                          f"Sleep {e.retry_after} seconds."
#                          )
#             await asyncio.sleep(e.retry_after)
#             await message.answer(f"{count}, {user.uuid}, {user.first_name}, {user.role}\n")
#             count = count + 1
#         except TelegramForbiddenError:
#             logger.info(f"Target [ID:{user.uuid}]: Bot Blocked")
#
#     logger.info(f"{count - 1} messages successful sent.")
#     return count - 1


T = TypeVar("T")


def split_into_chunks(
        items: Iterable[T],
        render: Callable[[int, T], str],
        limit: int = settings.MAX_MESSAGE_LENGTH,
) -> tuple[list[str], int]:
    """
    Разбивает список объектов на текстовые чанки ≤ limit символов.
    render(index, item) -> строка для одного элемента.
    """

    # def split_into_chunks(items, render, limit) -> tuple[list[str], int]:
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    total_items = 0

    for index, item in enumerate(items, start=1):
        line = render(index, item)
        if current_len + len(line) > limit:
            chunks.append("".join(current))
            current.clear()
            current_len = 0
        current.append(line)
        current_len += len(line)
        total_items += 1

    if current:
        chunks.append("".join(current))

    return chunks, total_items


def split_strings_into_chunks(
    lines: Iterable[str],
    limit: int = settings.MAX_MESSAGE_LENGTH,
) -> tuple[list[str], int]:
    """
    Разбивает готовые строки на чанки ≤ limit символов.
    """
    limit = int(limit)
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    total_lines = 0

    for line in lines:
        if not line.endswith("\n"):
            line = line + "\n"
        if current_len + len(line) > limit:
            chunks.append("".join(current))
            current.clear()
            current_len = 0
        current.append(line)
        current_len += len(line)
        total_lines += 1

    if current:
        chunks.append("".join(current))

    return chunks, total_lines

# async def send_users_list(message: Message, users: list[User]) -> int:
#     chunks = split_into_chunks(users)
#
#     sent = 0
#     for chunk in chunks:
#         try:
#             await message.answer(chunk)
#             sent += 1
#         except TelegramRetryAfter as e:
#             logger.error(f"Flood limit. Sleep {e.retry_after}s.")
#             await asyncio.sleep(e.retry_after)
#             await message.answer(chunk)
#             sent += 1
#         except TelegramForbiddenError:
#             logger.info("Bot blocked by recipient.")
#
#     logger.info(f"{sent} messages successfully sent.")
#     return sent


async def send_chunks(message: Message, chunks: list[str]) -> int:
    sent = 0
    for chunk in chunks:
        try:
            await message.answer(chunk)
            sent += 1
        except TelegramRetryAfter as e:
            logger.error(f"Flood limit. Sleep {e.retry_after}s.")
            await asyncio.sleep(e.retry_after)
            await message.answer(chunk)
            sent += 1
        except TelegramForbiddenError:
            logger.info("Bot blocked by recipient.")
    logger.info(f"{sent} messages successfully sent.")
    return sent


# рабочий
async def send_users_list_4096(message: Message, users: list[User]) -> int:
    count: int = 1
    string_users: list[str] = []
    strings_list: list[str] = []
    for user in users:
        if len(f"{count}, {user.uuid}, {user.first_name}, {user.role.name}, {user.registration}\n") + len(
                "".join(string_users)) < 4096:
            string_users.append(f"{count}, {user.uuid}, {user.first_name}, {user.role.name}, {user.registration}\n")
            if len(users) == count:
                strings_list.append("".join(string_users))
        else:
            strings_list.append("".join(string_users))
            string_users.clear()
            string_users.append(f"{count}, {user.uuid}, {user.first_name}, {user.role.name}, {user.registration}\n")
            if len(users) == count:
                strings_list.append("".join(string_users))
        count += 1
    for item in strings_list:
        try:
            await message.answer(item)
            # count = count + 1
        except TelegramRetryAfter as e:
            logger.error(f"Target: Flood limit is exceeded. "
                         f"Sleep {e.retry_after} seconds."
                         )
            await asyncio.sleep(e.retry_after)
            await message.answer(item)
            count = count + 1
        except TelegramForbiddenError:
            logger.info(f"Target [ID:{user.uuid}]: Bot Blocked")

    logger.info(f"{count - 1} messages successful sent.")
    return count - 1
