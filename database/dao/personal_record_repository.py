from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import PersonalRecordCard
from database.connection import connection


class PersonalRecordDAO:
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
