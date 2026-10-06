import logging
from typing import Any, ClassVar, Type, TypeVar, Generic, cast

from sqlalchemy import select, delete, and_, update, CursorResult
from sqlalchemy.exc import SQLAlchemyError, DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from models import Base, PoolQuestion

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Base)


class BaseDAO(Generic[T]):
    """
        # model = None  # Устанавливается в дочернем классе

    """
    table_name = None
    name_field: str
    model: type[T]

    @classmethod
    async def add(cls, session: AsyncSession, data: Base | dict) -> T:
        if isinstance(data, cls.model):
            instance = data
        elif isinstance(data, dict):
            instance = cls.model(**data)
        else:
            raise TypeError(
                f"data must be {cls.model.__name__} or dict, got {type(data).__name__}"
            )
        try:
            session.add(instance)
            await session.commit()
        except SQLAlchemyError:
            await session.rollback()
            raise
        return instance

    @classmethod
    async def add_many(cls, session: AsyncSession, data: list[Base | dict]) -> list[T]:
        instances = []
        for item in data:
            if isinstance(item, cls.model):
                instances.append(item)
            elif isinstance(item, dict):
                instances.append(cls.model(**item))
            else:
                raise TypeError(
                    f"item must be {cls.model.__name__} or dict, got {type(item).__name__}"
                )
        try:
            session.add_all(instances)
            await session.commit()
        except SQLAlchemyError:
            await session.rollback()
            raise
        return instances

    @classmethod
    async def get_by_id(cls, session: AsyncSession, id_: Any) -> T | None:
        return await session.get(cls.model, id_)

    @classmethod
    async def delete_by_id(cls, session: AsyncSession, id_: int) -> int:
        stmt = delete(cls.model).where(cls.model.id == id_)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount  # type: ignore

    @classmethod
    async def update_by_id(cls, session: AsyncSession, id_: int, **values) -> int:
        stmt = (
            update(cls.model)
            .where(cls.model.id == id_)
            .values(**values)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount  # type: ignore

    @classmethod
    async def delete_by_user_and_pool(cls, session: AsyncSession, **kwargs):
        stmt = delete(cls.model).where(and_(cls.model.user_uuid == kwargs["user_uuid"],
                                            cls.model.pool_id == kwargs["pool_id"]))
        await session.execute(stmt)
        await session.commit()

    # @classmethod
    # async def get_by_link_id(cls, session: AsyncSession, **kwargs) -> list[Any]:
    #
    #     stmt = select(PoolQuestion).where(PoolQuestion.pool_id == 50)
    #     result = await session.execute(stmt)
    #
    #     return []
