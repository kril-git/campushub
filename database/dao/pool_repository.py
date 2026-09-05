# import logging
# from datetime import datetime
# from typing import Any, Sequence
#
# from sqlalchemy import select, Result, and_, update
# from sqlalchemy.ext.asyncio import AsyncSession
# from database.connection import connection
# from database.dao.base_repository import BaseRepository
# from database.dao.dao import PoolDAO, PoolQuestionDAO, PoolAnswerDAO, AnswerDAO, UserPoolDAO
# from models import Pool, PoolQuestion, PoolAnswer, Answer, UserPool
# from services import EnumPools
# from services.EnumPoolAction import PoolAction
# from services.EnumPools import PoolCategory
#
# logger = logging.getLogger(__name__)
#
#
# # @connection
# # async def create_record(session: AsyncSession, obj: Any) -> Any:
# #     instance = obj
# #     session.add(instance)
# #     await session.flush()
# #     await session.commit()
# #     return instance
# #
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
#
#
# class DAOPools:
#
#     @staticmethod
#     @connection
#     async def get_pool_id_action(session: AsyncSession, pool_category: PoolCategory) -> int:
#         return await PoolDAO.get_id_action(session=session, pool_category=pool_category)
#
#     @staticmethod
#     @connection
#     async def get_pool_uuid_action(session: AsyncSession, pool_category: PoolCategory) -> str:
#         return await PoolDAO.get_uuid_action(session=session, pool_category=pool_category)
#
#     @staticmethod
#     @connection
#     async def add_pool_record(session: AsyncSession, data: Pool) -> Any:
#         pool_id: int = await DAOPools.get_pool_id_action(pool_category=data.pool_category)
#         if pool_id is not None:
#             await PoolDAO.update_category(session=session, pool_id=pool_id)
#
#         instance = await PoolDAO.add(session=session, data=data)
#         return instance
#
#     @staticmethod
#     @connection
#     async def add_pool_question(session: AsyncSession, data: PoolQuestion) -> Any:
#         instance = await PoolQuestionDAO.add(session=session, data=data)
#         return instance
#
#     @staticmethod
#     @connection
#     async def add_pool_answer(session: AsyncSession, data: list[PoolAnswer]) -> Any:
#         instance = await PoolAnswerDAO.add_many(session=session, data=data)
#         return instance
#
#     @staticmethod
#     @connection
#     async def get_pool(session: AsyncSession, **kwargs) -> Pool:
#         stmt = (select(Pool).where(and_(Pool.pool_category == kwargs["category"],
#                                         Pool.pool_action == PoolAction.ACTION))
#                 )
#         result: Result = await session.execute(stmt)
#         # users = await session.scalars(stmt)
#         return result.scalar()
#
#     @staticmethod
#     @connection
#     async def get_by_link_id(session: AsyncSession, link_id: int) -> list:
#         data = await PoolQuestionDAO.get_by_link_id(session=session, link_id=link_id)
#         return data
#
#     @staticmethod
#     async def create_one_record(data: dict) -> bool:
#         print(data["question"])
#         for i in data["answers"]:
#             print(i)
#         return False
#
#     @staticmethod
#     @connection
#     async def get_object_pool(session: AsyncSession, id_pool: int) -> Pool:
#         data = await PoolDAO.get_object_pool(session=session, id_pool=id_pool)
#         return data
#
#     @staticmethod
#     @connection
#     async def get_object_pool_question_by_pool_id(session: AsyncSession, pool_id: int) -> Sequence[PoolQuestion]:
#         data = await PoolQuestionDAO.get_object_pool_question_by_pool_id(session=session, pool_id=pool_id)
#         return data
#
#     @staticmethod
#     @connection
#     async def get_object_pool_question_by_pool_id_and_number_q(session: AsyncSession, pool_id: int,
#                                                                number_q: int) -> PoolQuestion:
#         data = await PoolQuestionDAO.get_object_pool_question_by_pool_id_and_number_q(session=session, pool_id=pool_id,
#                                                                                       number_q=number_q)
#         return data
#
#     @staticmethod
#     @connection
#     async def get_object_pool_answer_by_question_id(session: AsyncSession, question_id: int) -> list[PoolAnswer]:
#         data = await PoolAnswerDAO.get_object_pool_answer_by_question_id(session=session, question_id=question_id)
#         return list(data)
#
#     @staticmethod
#     @connection
#     async def get_count_questions(session: AsyncSession, pool_id: int) -> int:
#         data = await PoolQuestionDAO.get_count_questions(session=session, pool_id=pool_id)
#         return data
#
#     @staticmethod
#     @connection
#     async def get_object_pool_answer_by_id(session: AsyncSession, answer_id: int) -> PoolAnswer:
#         data = await PoolAnswerDAO.get_object_pool_answer_by_id(session=session, answer_id=answer_id)
#         return data
#
#     @staticmethod
#     @connection
#     async def add_user_answer(session: AsyncSession, data: list[Answer]) -> Any:
#         instance = await AnswerDAO.add_many(session=session, data=data)
#         return instance
#
#     @staticmethod
#     @connection
#     async def add_user_pools_record(session: AsyncSession, data: UserPool) -> UserPool:
#         instance = await UserPoolDAO.add(session=session, data=data)
#         return instance
#
#     @staticmethod
#     @connection
#     async def check_survey_completion(session: AsyncSession, **kwargs) -> bool:
#         """
#         Вернет False если пользователь не проходил опрос
#         """
#         if await UserPoolDAO.get_check_survey_completion(session=session, **kwargs) is None:
#             return False
#         else:
#             return True
#
#     @staticmethod
#     @connection
#     async def delete_user_pool(session: AsyncSession, **kwargs):
#         await UserPoolDAO.delete_by_user_and_pool(session=session,
#                                                   user_uuid=kwargs["user_uuid"],
#                                                   pool_id=kwargs["pool_id"])
#         await AnswerDAO.delete_by_user_and_pool(session=session,
#                                                 user_uuid=kwargs["user_uuid"],
#                                                 pool_id=kwargs["pool_id"])
#
#     @staticmethod
#     @connection
#     async def get_answer_by_user_id(session: AsyncSession, **kwargs):
#         result = await AnswerDAO.get_answer_by_user_id(session=session, user_uuid=kwargs["user_uuid"])
#         return result
