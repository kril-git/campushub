from datetime import datetime
from typing import Sequence

from sqlalchemy import select, Result, update, and_, func, RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from database.dao.base import BaseDAO
from models import Pool, PoolQuestion, PoolAnswer, Answer, UserPool
from services import EnumPools
from services.EnumPoolAction import PoolAction


class PoolDAO(BaseDAO):
    model = Pool

    @classmethod
    async def get_id_action(cls, session: AsyncSession, pool_category: EnumPools) -> int | None:
        stmt = (
            select(Pool.id).where(Pool.pool_action == PoolAction.ACTION and Pool.pool_category == pool_category)
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

    @staticmethod
    async def update_category(session: AsyncSession, pool_id: int):
        stmt = (
            update(Pool).where(Pool.id == pool_id).values(pool_action=PoolAction.DELETE, date_update=datetime.now())
        )
        result: Result = await session.execute(stmt)
        return result

    @staticmethod
    async def get_object_pool(session: AsyncSession, id_pool: int) -> Pool:
        stmt = select(Pool).where(and_(Pool.pool_action == PoolAction.ACTION, Pool.id == id_pool))
        result = await session.execute(stmt)
        return result.scalar()


class PoolQuestionDAO(BaseDAO):
    model = PoolQuestion
    name_field = "pool_id"
    table_name = "poolquestions"

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


class PoolAnswerDAO(BaseDAO):
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


class AnswerDAO(BaseDAO):
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


class UserPoolDAO(BaseDAO):
    model = UserPool

    @classmethod
    async def get_check_survey_completion(cls, session: AsyncSession, **kwargs) -> Result | None:
        stmt = select(cls.model).where(and_(cls.model.user_uuid == kwargs["user_uuid"],
                                            cls.model.pool_id == kwargs["pool_id"]))
        result = await session.execute(stmt)
        return result.one_or_none()
