import logging

# from database.dao.base_repository import BaseRepository

logger = logging.getLogger(__name__)


# @connection
# async def create_record(session: AsyncSession, obj: Any) -> Any:
#     instance = obj
#     session.add(instance)
#     await session.flush()
#     await session.commit()
#     return instance
#

# class PoolRepository(BaseRepository):
#     """Репозиторий для работы с опросами (Pools)."""
#     model: Pool = Pool
#
#     def __init__(self):
#         # Передаем модель Pool в родительский класс
#         super().__init__(model=self.model)
#
#     @classmethod
#     @connection
#     async def get_id_pool_action(cls, session: AsyncSession, pool_category: EnumPools) -> int | None:
#         stmt = (
#             select(Pool.id).where(Pool.pool_action == PoolAction.ACTION and Pool.pool_category == pool_category)
#         )
#         result = await session.execute(stmt)
#         id_pool = result.scalar()
#         return id_pool
#
#     @classmethod
#     @connection
#     async def update_pool_action(cls, session: AsyncSession, pool_id: int):
#         stmt = (
#             update(cls.model).where(cls.model.id == pool_id).values(pool_action=PoolAction.DELETE, date_update=datetime.now())
#         )
#         result: Result = await session.execute(stmt)
#         return result


