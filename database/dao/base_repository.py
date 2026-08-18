import logging

from sqlalchemy import select, Result
from sqlalchemy.exc import SQLAlchemyError, DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import connection
from models import Base

logger = logging.getLogger(__name__)


class BaseRepository[T: Base]:
    model: [T]

    def __init__(self, model):
        self.model = model

    @classmethod
    @connection
    async def get_by_id(cls, session: AsyncSession, obj_id: int):
        """
        Получить объект по ID.
        """
        stmt = select(cls.model).where(cls.model.id == obj_id)
        result: Result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    @connection
    async def add(cls, session: AsyncSession, data: Base | None, **kwargs):
        """
        Добавить одну запись
        """

        if data is not None:
            new_instance = data
        else:
            new_instance = cls.model(**kwargs)
        session.add(new_instance)
        try:
            await session.commit()
            logger.info(f"add")
        except SQLAlchemyError as e:
            await session.rollback()
            raise e
        except DBAPIError as e:
            await session.rollback()
            raise e
        return new_instance


