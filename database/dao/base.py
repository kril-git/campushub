import logging
from typing import Any

from sqlalchemy import select, delete, and_
from sqlalchemy.exc import SQLAlchemyError, DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from models import Base, PoolQuestion

logger = logging.getLogger(__name__)


class BaseDAO[T: Base]:
    """
        # model = None  # Устанавливается в дочернем классе

    """
    table_name = None
    model: [T]
    name_field: str

    @classmethod
    async def add(cls, session: AsyncSession, data: Base | None, **kwargs):
        # Добавить одну запись
        if data is not None:
            new_instance = data
        else:
            new_instance = cls.model(**kwargs)
        session.add(new_instance)
        try:
            # pass
            await session.commit()
            logger.info(f"add")
        except SQLAlchemyError as e:
            await session.rollback()
            raise e
        except DBAPIError as e:
            await session.rollback()
            raise e
        return new_instance

    @classmethod
    async def add_many(cls, session: AsyncSession, data: list[Base], **kwargs) -> list[T]:
        if data is not None:
            new_instance = data
        else:
            new_instance = cls.model(**kwargs)
        session.add_all(new_instance)
        try:
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            raise e
        except DBAPIError as e:
            await session.rollback()
            raise e
        return new_instance

    @classmethod
    async def delete_by_user_and_pool(cls, session: AsyncSession, **kwargs):
        stmt = delete(cls.model).where(and_(cls.model.user_uuid == kwargs["user_uuid"],
                                            cls.model.pool_id == kwargs["pool_id"]))
        await session.execute(stmt)
        await session.commit()

    @classmethod
    async def get_by_link_id(cls, session: AsyncSession, **kwargs) -> list[Any]:

        stmt = select(PoolQuestion).where(PoolQuestion.pool_id == 50)
        result = await session.execute(stmt)

        return []
