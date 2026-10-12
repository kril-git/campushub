from typing import Sequence

from sqlalchemy import select, func, exists
from sqlalchemy.ext.asyncio import AsyncSession

from database.dao.base import BaseDAO
from dto.personal_record import PersonalRecordShort
from models import PersonalRecordCard
from database.connection import connection


class PersonalRecordDAO(BaseDAO[PersonalRecordCard]):
    model = PersonalRecordCard

    @classmethod
    async def get_by_uuid(
            cls, session: AsyncSession, uuid: str
    ) -> PersonalRecordCard | None:
        stmt = select(cls.model).where(cls.model.uuid == uuid)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def exists_by_uuid(cls, session: AsyncSession, uuid: str) -> bool:
        stmt = select(
            exists().where(cls.model.uuid == uuid)
        )
        return bool(await session.scalar(stmt))

    @staticmethod
    @connection
    async def get_short(
            session: AsyncSession,
    ) -> list[tuple[str, str, str, str]]:
        """Возвращает (uuid, surname, given_name, phone) для всех записей."""
        result = await session.execute(
            select(
                PersonalRecordCard.uuid,
                PersonalRecordCard.surname,
                PersonalRecordCard.given_name,
                PersonalRecordCard.phone,
            )
        )
        return list(result.tuples().all())

    @classmethod
    async def get_short_list(
            cls, session: AsyncSession
    ) -> Sequence[PersonalRecordShort]:
        stmt = select(
            cls.model.uuid,
            cls.model.surname,
            cls.model.given_name,
            cls.model.phone,
        )
        result = await session.execute(stmt)
        return [
            PersonalRecordShort(*row)
            for row in result.all()
        ]
