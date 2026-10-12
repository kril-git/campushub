from sqlalchemy import update, select, func, exists, Result
from sqlalchemy.ext.asyncio import AsyncSession

from database.dao.base import BaseDAO
from models import User
from utils.converters import uuid_to_str


class UserDAO(BaseDAO[User]):
    model = User

    @classmethod
    async def mark_registered(cls, session: AsyncSession, uuid: str) -> None:
        stmt = (
            update(cls.model)
            .where(cls.model.uuid == uuid)
            .values(registration=True)
        )
        await session.execute(stmt)

    @classmethod
    async def exists_by_uuid(cls, session: AsyncSession, uuid: str) -> bool:
        stmt = select(
            exists().where(cls.model.uuid == uuid)
        )
        return bool(await session.scalar(stmt))

    @classmethod
    async def get_by_uuid(cls, session: AsyncSession, uuid: str) -> User | None:
        stmt = select(cls.model).where(cls.model.uuid == uuid)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def is_registered(cls, session: AsyncSession, uuid: str) -> bool:
        stmt = select(User.registration).where(User.uuid == uuid)
        result: Result = await session.execute(stmt)
        is_registered: bool = result.scalar().one_or_none()
        return is_registered
