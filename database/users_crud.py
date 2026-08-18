import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select, Result, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import connection
from models import User
from services.EnumRoles import Roles

logger = logging.getLogger(__name__)


@connection
# async def if_exist_user(uuid: str | int, session: Optional[AsyncSession] = None) -> bool:
async def if_exist_user(session: Optional[AsyncSession], uuid: str | int) -> bool:
    """
    :param session:
    :param uuid: уникальный номер пользователя
    :return: true or false
    """

    if isinstance(uuid, int):
        stmt = select(User).where(User.uuid == str(uuid))
    else:
        stmt = select(User).where(User.uuid == uuid)
    result: Result = await session.execute(stmt)
    user: User | None = result.one_or_none()
    if user is None:
        return False
    else:
        return True


@connection
async def create_new_user(session: AsyncSession, user: User) -> User:
    session.add(user)
    await session.commit()
    return user


@connection
async def get_user_by_uuid(session: AsyncSession, uuid: str | int) -> User:
    if isinstance(uuid, int):
        stmt = select(User).where(User.uuid == str(uuid))
    else:
        stmt = select(User).where(User.uuid == uuid)
    result: Result = await session.execute(stmt)
    user: User = result.scalar()
    return user


@connection
async def update_last_visit(session: AsyncSession, uuid: str | int):
    if isinstance(uuid, int):
        stmt = (
            update(User).where(User.uuid == str(uuid)).values(last_visit=datetime.now())
        )
    else:
        stmt = (
            update(User).where(User.uuid == uuid).values(last_visit=datetime.now())
        )
    await session.execute(stmt)
    await session.commit()


@connection
async def get_users_by_role(session: AsyncSession, role: Roles | None = Roles.ADMIN.name) -> list[str]:
    stmt = (
        select(User.uuid).where(User.role == role)
    )
    result = await session.execute(stmt)
    uuids: list = list(result.scalars().all())
    return uuids
