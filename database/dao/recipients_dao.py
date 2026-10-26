from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.dao.base import BaseDAO
from models import PersonalRecordCard, UserPool


class RecipientsDAO(BaseDAO[PersonalRecordCard]):
    model = PersonalRecordCard

    @classmethod
    async  def get_real_recipients(cls, session: AsyncSession) -> list[str]:
        """
        Все зарегистрированные пользователи (uuid = telegram_id, unique=True).
        Это ровно те, кто нажимал /start — бот может им писать.
        """

        stmt = (
            select(cls.model.uuid)
            .where(cls.model.uuid.is_not(None))
            .where(cls.model.uuid != "")
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    # database/dao/recipients_dao.py
    @classmethod
    async def get_recipients_excluding_completed(
            cls, session: AsyncSession, pool_id: int
    ) -> Sequence[str]:
        """
        Все telegram_id, кто НЕ прошёл опрос pool_id
        (нет записи UserPool с end_pool=True).
        """
        stmt = (
            select(PersonalRecordCard.uuid)
            .outerjoin(
                UserPool,
                (UserPool.user_uuid == PersonalRecordCard.uuid)
                & (UserPool.pool_id == pool_id)
                & (UserPool.end_pool.is_(True)),
            )
            .where(
                PersonalRecordCard.uuid.is_not(None),
                PersonalRecordCard.uuid != "",
                UserPool.id.is_(None),  # ← нет прохождения
            )
        )
        result = await session.execute(stmt)
        return result.scalars().all()
