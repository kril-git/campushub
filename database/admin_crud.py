import logging
from typing import Sequence

from sqlalchemy import select, Result, update, and_, RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import connection
from database.users_crud import get_user_by_uuid
from models import User, UserPool, Pool
from services.EnumRoles import Roles
from core.config import settings

logger = logging.getLogger(__name__)


@connection
async def set_role(session: AsyncSession, uuid: str | int) -> User:
    if isinstance(uuid, int):
        stmt = (
            update(User).where(User.uuid == str(uuid)).values(role=Roles.ADMIN)
        )
    else:
        stmt = (
            update(User).where(User.uuid == str(uuid)).values(role=Roles.ADMIN)
        )
    await session.execute(stmt)
    await session.commit()
    user = await get_user_by_uuid(uuid=uuid)
    settings.ADMINS.append(str(user.uuid))
    return user


@connection
async def get_user_all(session: AsyncSession) -> list[User]:
    stmt = (select(User))
    result: Result = await session.execute(stmt)
    # users = await session.scalars(stmt)
    return list(result.scalars().all())


@connection
async def get_user_by_uuid(session: AsyncSession, uuid: str | int) -> User | None:
    stmt = select(User).where(User.uuid == str(uuid))
    result: Result = await session.execute(stmt)
    user: User | None = result.scalar_one_or_none()
    return user


@connection
async def get_users_pools_all_or_one(session: AsyncSession, user_uuid: str | None) -> list[UserPool]:
    if user_uuid is None:
        stmt = select(UserPool).where(UserPool.end_pool == bool(True)).order_by(UserPool.user_uuid)
    else:
        stmt = (select(UserPool)
                .where(and_(UserPool.end_pool == bool(True), UserPool.user_uuid == user_uuid))
                .order_by(UserPool.user_uuid))
    result = await session.execute(stmt)
    return list(result.scalars().all())


@connection
async def get_users_pools_join_user(session: AsyncSession, user_uuid: str | None = None) -> Sequence[RowMapping]:
    if user_uuid is None:
        stmt = (select(UserPool.pool_id,
                       UserPool.user_uuid,
                       UserPool.user_uuid,
                       UserPool.step,
                       UserPool.end_pool,
                       User.first_name,
                       Pool.pool_category)
                .where(UserPool.end_pool == bool(True))
                .join(User, User.uuid == UserPool.user_uuid)
                .join(Pool, Pool.id == UserPool.pool_id)
                .order_by(UserPool.user_uuid))
    else:
        stmt = (select(UserPool.pool_id,
                       UserPool.user_uuid,
                       UserPool.user_uuid,
                       UserPool.step,
                       UserPool.end_pool,
                       User.first_name)
                .where(and_(UserPool.end_pool == bool(True), UserPool.user_uuid == user_uuid))
                .join(User, User.uuid == UserPool.user_uuid)
                .order_by(UserPool.user_uuid))
    result = await session.execute(stmt)

    return result.mappings().all()
