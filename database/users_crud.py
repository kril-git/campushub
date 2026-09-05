import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select, Result, update
from sqlalchemy.exc import ProgrammingError, NoSuchTableError
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from database.connection import connection
from models import User, PersonalRecordCard
from services.EnumRoles import Roles

logger = logging.getLogger(__name__)


@connection
async def if_exist_user(session: Optional[AsyncSession], uuid: str | int) -> bool | None:
    """
    :param session:
    :param uuid: уникальный номер пользователя
    :return: true or false
    """
    if session is None:
        return None
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
    try:
        stmt = (
            select(User.uuid).where(User.role == role)
        )
        result = await session.execute(stmt)
        uuids: list = list(result.scalars().all())
        return uuids
    except (ProgrammingError, NoSuchTableError) as e:
        logger.error(f"Таблица не найдена: {e}")
        return settings.ADMINS.append(settings.MAIN_ADMIN)
    except Exception as e:
        logger.error(f"Другая ошибка: {e}")
        return settings.ADMINS.append(settings.MAIN_ADMIN)


@connection
async def save_user_registration(session: AsyncSession, user_data: dict, uuid: str) -> PersonalRecordCard:
    """
    Сохраняет данные регистрации пользователя
    """
    try:
        # ✅ Добавляем uuid в данные
        user_data["uuid"] = uuid
        birth_date_str = user_data["birth_date"]
        date_obj = datetime.strptime(birth_date_str, "%d.%m.%Y").date()
        user_data["birth_date"] = date_obj

        # ✅ Логируем данные для отладки
        logger.info(f"Сохранение данных пользователя {uuid}:")
        # for key, value in user_data.items():
        #     logger.info(f"  {key}: {value}")

        # ✅ СОЗДАЕМ И ПРИСВАИВАЕМ объект
        registration_field = PersonalRecordCard(**user_data)

        # ✅ Проверяем, что объект создан
        if registration_field is None:
            logger.error("❌ Не удалось создать PersonalRecordCard")
            return None

        # ✅ Добавляем в сессию
        session.add(registration_field)
        await session.commit()
        await session.refresh(registration_field)

        logger.info(f"✅ Данные пользователя {uuid} сохранены")
        return registration_field

    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении данных пользователя {uuid}: {e}")
        await session.rollback()
        return None
