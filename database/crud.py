from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import connection
from database.dao.dao import PoolDAO
from models import Base


@connection
async def add_one(session: AsyncSession, data: dict | Base) -> Any:
    if isinstance(data, Base):
        print(f"Добавлеа запись из Обьекта")
        instance = await PoolDAO.add(session=session, data=data)
        return instance
    elif isinstance(data, dict):
        instance = await PoolDAO.add(session=session, **data)

        print(f"Добавлеа запись с ID: {instance.id}")
        return instance
