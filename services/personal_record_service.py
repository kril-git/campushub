# services/personal_record_service.py
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import connection, readonly
from database.dao.personal_record_dao import PersonalRecordDAO
from database.dao.users_dao import UserDAO
from models import PersonalRecordCard
from services.render import render_personal_record
# from database.dao

import logging

from validators.personal_record_validator import PersonalRecordValidator

logger = logging.getLogger(__name__)


class PersonalRecordService:

    @staticmethod
    @connection
    async def save_user_registration(
        session: AsyncSession, user_data: dict, uuid: str
    ) -> PersonalRecordCard | None:
        # 1. Проверить, что User существует
        if not await UserDAO.exists_by_uuid(session, uuid):
            logger.warning("User %s не найден", uuid)
            return None

        # 2. Подготовить данные (валидация + парсинг + uuid)
        try:
            data = PersonalRecordValidator.validate_and_prepare(user_data, uuid)
        except ValueError as e:
            logger.warning("Ошибка валидации: %s", e)
            raise   # или вернуть None, если сервис сам решает

        # 3. Создать карту
        card = PersonalRecordCard(**data)
        card = await PersonalRecordDAO.add(session, card)

        # 4. Пометить пользователя зарегистрированным
        await UserDAO.mark_registered(session, uuid)

        return card
        # commit сделает @connection

    @staticmethod
    @readonly
    async def get_short_list_text(session: AsyncSession) -> list[str]:
        rows = await PersonalRecordDAO.get_short_list(session)
        return [row.format_line(i) for i, row in enumerate(rows, start=1)]


async def get_personal_record_short_lines() -> list[str]:
    """Возвращает отформатированные строки для Telegram."""
    rows = await PersonalRecordDAO.get_short()
    return [
        f"{i}, {uuid}, {surname}, {given_name}, {phone}\n"
        for i, (uuid, surname, given_name, phone) in enumerate(rows, start=1)
    ]


async def get_personal_record_short_lines_render() -> list[str]:
    """
    Пример распаковки используя рэндер
    """
    rows = await PersonalRecordDAO.get_short()
    return [
        render_personal_record(i, row)
        for i, row in enumerate(rows, start=1)
    ]
