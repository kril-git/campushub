from datetime import datetime
from typing import Sequence, Any

from sqlalchemy import select, Result, update, and_, func, RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import connection
from database.dao.base import BaseDAO
from models import Pool, PoolQuestion, PoolAnswer, Answer, UserPool
from services import EnumPools
from services.EnumPoolAction import PoolAction
from services.EnumPools import PoolCategory


class PoolDAO(BaseDAO[Pool]):
    model = Pool

    @classmethod
    async def add_pool_record(cls, session: AsyncSession, data: Pool) -> Pool:
        pool_id = await cls.get_id_action(
            session=session,
            pool_category=data.pool_category,
        )
        if pool_id is not None:
            await cls.mark_as_deleted(session=session, pool_id=pool_id)
        # await cls.add(session=session, data=data)
        # await session.flush()
        return await cls.add(session=session, data=data)

    @classmethod
    async def get_id_action(cls, session: AsyncSession, pool_category: EnumPools) -> int | None:
        stmt = (
            select(Pool.id).where(and_(cls.model.pool_action == PoolAction.ACTION,
                                       cls.model.pool_category == pool_category))
        )
        result = await session.execute(stmt)
        id_pool = result.scalar()
        return id_pool

    @classmethod
    async def get_uuid_action(cls, session: AsyncSession, pool_category: EnumPools) -> str | None:
        stmt = (
            select(Pool.pool_uuid).where(Pool.pool_action == PoolAction.ACTION and Pool.pool_category == pool_category)
        )
        result = await session.execute(stmt)
        uuid_pool: str | None = result.one_or_none()
        return uuid_pool

    @classmethod
    async def mark_as_deleted(cls, session: AsyncSession, pool_id: int):
        stmt = (
            update(cls.model)
            .where(cls.model.id == pool_id)
            .values(pool_action=PoolAction.DELETE, date_update=datetime.now())
        )
        result: Result = await session.execute(stmt)
        return result

    @classmethod
    async def get_object_pool(cls, session: AsyncSession, id_pool: int) -> Pool | None:
        stmt = (select(cls.model)
                .where(cls.model.pool_action == PoolAction.ACTION, cls.model.id == id_pool))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


class PoolQuestionDAO(BaseDAO[PoolQuestion]):
    model = PoolQuestion
    name_field = "pool_id"
    table_name = "poolquestions"

    @classmethod
    async def add_pool_question(cls, session: AsyncSession, data: PoolQuestion) -> PoolQuestion:
        return await cls.add(session=session, data=data)

    @staticmethod
    async def get_object_pool_question_by_pool_id(session: AsyncSession, pool_id: int) -> Sequence[PoolQuestion]:
        stmt = select(PoolQuestion).where(PoolQuestion.pool_id == pool_id)
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_object_pool_question_by_pool_id_and_number_q(session: AsyncSession,
                                                               pool_id: int,
                                                               number_q: int) -> PoolQuestion:
        stmt = select(PoolQuestion).where(
            and_(PoolQuestion.pool_id == pool_id, PoolQuestion.question_number == number_q))
        result = await session.execute(stmt)
        return result.scalars().one()

    @staticmethod
    async def get_count_questions(session: AsyncSession, pool_id: int) -> int:
        stmt = select(func.count(PoolQuestion.pool_id)).select_from(PoolQuestion).where(PoolQuestion.pool_id == pool_id)
        result = await session.scalar(stmt)
        return result


class PoolAnswerDAO(BaseDAO[PoolAnswer]):
    model = PoolAnswer

    @staticmethod
    async def get_object_pool_answer_by_question_id(session: AsyncSession, question_id) -> Sequence[model]:
        stmt = select(PoolAnswer).where(PoolAnswer.pool_question_id == question_id)
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_object_pool_answer_by_id(session: AsyncSession, answer_id: int) -> PoolAnswer:
        stmt = select(PoolAnswer).where(PoolAnswer.id == answer_id)
        result = await session.execute(stmt)
        return result.scalar()


class AnswerDAO(BaseDAO[Answer]):
    model = Answer

    @classmethod
    async def get_answer_by_user_id(cls, session: AsyncSession, **kwargs) -> Sequence[RowMapping]:
        stmt = (select(Answer.pool_id,
                       PoolQuestion.question_number,
                       PoolQuestion.pool_question,
                       PoolAnswer.pool_answer)
                .where(Answer.user_uuid == kwargs["user_uuid"])
                .join(PoolQuestion, Answer.question_id == PoolQuestion.id)
                .join(PoolAnswer, Answer.answer_id == PoolAnswer.id)
                ).order_by(PoolQuestion.question_number)
        result = await session.execute(stmt)
        return result.mappings().all()


class UserPoolDAO(BaseDAO[UserPool]):
    model = UserPool

    @classmethod
    async def get_check_survey_completion(cls, session: AsyncSession, **kwargs) -> Result | None:
        stmt = select(cls.model).where(and_(cls.model.user_uuid == kwargs["user_uuid"],
                                            cls.model.pool_id == kwargs["pool_id"]))
        result = await session.execute(stmt)
        return result.one_or_none()


class DAOPools:

    # ---------- приватные: принимают сессию, содержат логику ----------

    # @staticmethod
    # async def _get_pool_action(session: AsyncSession, pool_category: PoolCategory) -> Pool | None:
    #     # async def get_pool(session: AsyncSession, **kwargs) -> Pool:
    #     stmt = (select(Pool).where(and_(Pool.pool_category == pool_category,
    #                                     Pool.pool_action == PoolAction.ACTION))
    #             )
    #     result: Result = await session.execute(stmt)
    #     # users = await session.scalars(stmt)
    #     return result.scalar()

    @staticmethod
    async def _update_pool_actions(session: AsyncSession, id: int):
        """
        Закрывает опрос если дата окончания опроса меньше чем сегодня.
        """
        stmt = (
            update(Pool).where(Pool.id == id).values(pool_action=PoolAction.DELETE, date_update=datetime.now())
        )
        result: Result = await session.execute(stmt)
        await session.commit()
        return result

    # ---------- публичные: сессия от декоратора ----------

    # @staticmethod
    # @connection
    # async def get_pool_action(_session: AsyncSession, pool_category: PoolCategory) -> Pool | None:
    #     return await DAOPools._get_pool_action(session=_session, pool_category=pool_category)

    @staticmethod
    @connection
    async def update_pool_actions(_session: AsyncSession, id: int):
        return await DAOPools._update_pool_actions(session=_session, id=id)

    @staticmethod
    async def get_pool_id(session: AsyncSession, pool_category: PoolCategory) -> int:
        """Внутренний — session передаётся явно."""
        return await PoolDAO.get_id_action(session=session, pool_category=pool_category)

    @staticmethod
    @connection
    async def get_pool_id_action(session: AsyncSession, pool_category: PoolCategory) -> int:
        """Публичный — сессия открывается декоратором."""
        return await DAOPools.get_pool_id(session=session, pool_category=pool_category)

    @staticmethod
    @connection
    async def add_pool_record(session: AsyncSession, data: Pool) -> Any:
        pool_id = await DAOPools.get_pool_id(  # ← внутренний, без _action
            session=session,
            pool_category=data.pool_category,
        )
        if pool_id is not None:
            await PoolDAO.mark_as_deleted(session=session, pool_id=pool_id)
        return await PoolDAO.add(session=session, data=data)

    # @staticmethod
    # # @connection
    # async def get_pool_id_action(session: AsyncSession, pool_category: PoolCategory) -> int:
    #     return await PoolDAO.get_id_action(session=session, pool_category=pool_category)
    #
    @staticmethod
    @connection
    async def get_pool_uuid_action(session: AsyncSession, pool_category: PoolCategory) -> str:
        return await PoolDAO.get_uuid_action(session=session, pool_category=pool_category)

    # @staticmethod
    # @connection
    # async def add_pool_record(session: AsyncSession, data: Pool) -> Any:
    #     pool_id: int = await DAOPools.get_pool_id_action(session=session, pool_category=data.pool_category)
    #     if pool_id is not None:
    #         await PoolDAO.update_category(session=session, pool_id=pool_id)
    #
    #     instance = await PoolDAO.add(session=session, data=data)
    #     return instance

    # @staticmethod
    # @connection
    # async def add_pool_question(session: AsyncSession, data: PoolQuestion) -> Any:
    #     instance = await PoolQuestionDAO.add(session=session, data=data)
    #     return instance

    # @staticmethod
    # @connection
    # async def add_pool_answer(session: AsyncSession, data: list[PoolAnswer]) -> Any:
    #     instance = await PoolAnswerDAO.add_many(session=session, data=data)
    #     return instance

    @staticmethod
    @connection
    async def get_pool(session: AsyncSession, **kwargs) -> Pool:
        stmt = (select(Pool).where(and_(Pool.pool_category == kwargs["category"],
                                        Pool.pool_action == PoolAction.ACTION))
                )
        result: Result = await session.execute(stmt)
        # users = await session.scalars(stmt)
        return result.scalar()

    # @staticmethod
    # @connection
    # async def get_by_link_id(session: AsyncSession, link_id: int) -> list:
    #     data = await PoolQuestionDAO.get_by_link_id(session=session, link_id=link_id)
    #     return data

    @staticmethod
    async def create_one_record(data: dict) -> bool:
        print(data["question"])
        for i in data["answers"]:
            print(i)
        return False

    @staticmethod
    @connection
    async def get_object_pool(session: AsyncSession, id_pool: int) -> Pool:
        data = await PoolDAO.get_object_pool(session=session, id_pool=id_pool)
        return data

    @staticmethod
    @connection
    async def get_object_pool_question_by_pool_id(session: AsyncSession, pool_id: int) -> Sequence[PoolQuestion]:
        data = await PoolQuestionDAO.get_object_pool_question_by_pool_id(session=session, pool_id=pool_id)
        return data

    @staticmethod
    @connection
    async def get_object_pool_question_by_pool_id_and_number_q(session: AsyncSession, pool_id: int,
                                                               number_q: int) -> PoolQuestion:
        data = await PoolQuestionDAO.get_object_pool_question_by_pool_id_and_number_q(session=session, pool_id=pool_id,
                                                                                      number_q=number_q)
        return data

    @staticmethod
    @connection
    async def get_object_pool_answer_by_question_id(session: AsyncSession, question_id: int) -> list[PoolAnswer]:
        data = await PoolAnswerDAO.get_object_pool_answer_by_question_id(session=session, question_id=question_id)
        return list(data)

    @staticmethod
    @connection
    async def get_count_questions(session: AsyncSession, pool_id: int) -> int:
        data = await PoolQuestionDAO.get_count_questions(session=session, pool_id=pool_id)
        return data

    @staticmethod
    @connection
    async def get_object_pool_answer_by_id(session: AsyncSession, answer_id: int) -> PoolAnswer:
        data = await PoolAnswerDAO.get_object_pool_answer_by_id(session=session, answer_id=answer_id)
        return data

    @staticmethod
    @connection
    async def add_user_answer(session: AsyncSession, data: list[Answer]) -> Any:
        instance = await AnswerDAO.add_many(session=session, data=data)
        return instance

    @staticmethod
    @connection
    async def add_user_pools_record(session: AsyncSession, data: UserPool) -> UserPool:
        instance = await UserPoolDAO.add(session=session, data=data)
        return instance

    @staticmethod
    @connection
    async def check_survey_completion(session: AsyncSession, **kwargs) -> bool:
        """
        Вернет False если пользователь не проходил опрос
        """
        if await UserPoolDAO.get_check_survey_completion(session=session, **kwargs) is None:
            return False
        else:
            return True

    @staticmethod
    @connection
    async def delete_user_pool(session: AsyncSession, **kwargs):
        await UserPoolDAO.delete_by_user_and_pool(session=session,
                                                  user_uuid=kwargs["user_uuid"],
                                                  pool_id=kwargs["pool_id"])
        await AnswerDAO.delete_by_user_and_pool(session=session,
                                                user_uuid=kwargs["user_uuid"],
                                                pool_id=kwargs["pool_id"])

    @staticmethod
    @connection
    async def get_answer_by_user_id(session: AsyncSession, **kwargs):
        result = await AnswerDAO.get_answer_by_user_id(session=session, user_uuid=kwargs["user_uuid"])
        return result
