from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.dao.base import BaseDAO
from models import ScheduledBroadcast
from services.EnumBroadcastStatus import BroadcastStatus


class ScheduledBroadcastDAO(BaseDAO[ScheduledBroadcast]):
    model = ScheduledBroadcast

    @classmethod
    async def get_pending(cls, session: AsyncSession, now: datetime) -> list[ScheduledBroadcast]:
        stmt = (
            select(cls.model)
            .where(cls.model.status == BroadcastStatus.PENDING)
            .where(cls.model.scheduled_at <= now)
            .order_by(cls.model.scheduled_at)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def mark_sent(cls, session: AsyncSession, broadcast_id: int) -> None:
        stmt = (
            update(cls.model)
            .where(cls.model.id == broadcast_id)
            .values(status=BroadcastStatus.SENT, sent_at=datetime.now())
        )
        await session.execute(stmt)

    @classmethod
    async def mark_failed(cls, session: AsyncSession, broadcast_id: int, error: str) -> None:
        stmt = (
            update(cls.model)
            .where(cls.model.id == broadcast_id)
            .values(status=BroadcastStatus.FAILED, error=error[:500])
        )
        await session.execute(stmt)

    @classmethod
    async def mark_cancelled(cls, session: AsyncSession, broadcast_id: int) -> None:
        stmt = (
            update(cls.model)
            .where(cls.model.id == broadcast_id)
            .values(status=BroadcastStatus.CANCELLED)
        )
        await session.execute(stmt)

    @classmethod
    async def get_by_id(cls, session: AsyncSession, broadcast_id: int) -> ScheduledBroadcast | None:
        return await session.get(cls.model, broadcast_id)

    @classmethod
    async def get_all_scheduled(cls, session: AsyncSession, limit: int = 20) -> list[ScheduledBroadcast]:
        """Все запланированные (pending), для админки."""
        stmt = (
            select(cls.model)
            .where(cls.model.status == BroadcastStatus.PENDING)
            .order_by(cls.model.scheduled_at)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())