import logging

from sqlalchemy import select, Result, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import connection
from database.users_crud import get_user_by_uuid
from models import User, PersonalRecordCard
from services.EnumRoles import Roles
from core.config import settings
import pandas as pd
from io import BytesIO

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
    user = await get_user_by_uuid(uuid=uuid)  # type: ignore
    settings.ADMINS.append(str(user.uuid))
    return user


#
#
@connection
async def get_user_all(session: AsyncSession) -> list[User]:
    stmt = (select(User))
    result: Result = await session.execute(stmt)
    # users = await session.scalars(stmt)
    return list(result.scalars().all())


@connection
async def export_users_to_excel(
        session: AsyncSession,
        filename: str = "users.xlsx",
        return_bytes: bool = False
):
    """
    Асинхронный экспорт пользователей в Excel

    Args:
        session: Передаётся через @connection
        filename: Имя файла для сохранения
        return_bytes: Если True - возвращает BytesIO
    """
    # 1. ORM-запрос (сессия уже передана)
    stmt = select(PersonalRecordCard)
    result = await session.execute(stmt)
    users = result.scalars().all()

    # 2. Формируем данные
    data = []
    for user in users:
        data.append({
            "Фамилия": user.surname or "",
            "Имя": user.given_name or "",
            "Отчество": user.middle_name or "",
            "Email": user.email or "",
            "Телефон": user.phone or "",
            "Дата рождения": user.birth_date or "",
            "Гражданство": user.nationality or "",
            "Место проживания": user.term_time_address or "",
            "Информация о родителях": user.parents_info or "",
            "Состояние семьи": user.status_family or "",
            "Многодетность": user.children or "",
            "Обеспеченность": user.low_income_family or "",
            "Инвалиды в семье": user.disability or "",
            "Член БРСМ": user.brsm or "",
            "Последствия ЧАЭС": user.cas or "",
        })

    # 3. Создаём DataFrame
    df = pd.DataFrame(data)

    if return_bytes:
        # Возвращает BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Пользователи")
        output.seek(0)
        return output
    else:
        # Возвращает строку
        df.to_excel("users.xlsx", index=False)
        return f"✅ Экспортировано {len(data)} записей в users.xlsx"
