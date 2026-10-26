from datetime import datetime, timedelta, date
from typing import Sequence, Any, cast

from sqlalchemy import select, Result, update, and_, func, RowMapping, delete, CursorResult, Date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.connection import connection
from database.dao.base import BaseDAO
from models import Pool, PoolQuestion, PoolAnswer, Answer, UserPool
from services import EnumPools
from services.EnumPoolAction import PoolAction
from services.EnumPools import PoolCategory


class PoolDAO(BaseDAO[Pool]):
    model = Pool

    @classmethod
    async def add_pool_record(cls, session: AsyncSession, data: Pool) -> model:
        # pool_id = await cls.get_id_action(
        #     session=session,
        #     pool_category=data.pool_category,
        # )
        # if pool_id is not None:
        #     await cls.mark_as_deleted(session=session, pool_id=pool_id)
        return await cls.add(session=session, data=data)

    @classmethod
    async def get_id_action(cls, session: AsyncSession, pool_category: EnumPools) -> int | None:
        today = date.today()
        stmt = (
            select(cls.model.id).where(and_(cls.model.pool_action == PoolAction.ACTION,
                                            cls.model.pool_category == pool_category,
                                            func.cast(cls.model.start_date, Date) <= today),
                                       func.cast(cls.model.end_date, Date) >= today
                                       ).limit(1)
        )
        result = await session.execute(stmt)
        id_pool = result.scalar()
        return id_pool

    @classmethod
    async def has_intersecting_pool(cls,
                                    session: AsyncSession,
                                    start: date,
                                    end: date,
                                    pool_category: EnumPools = PoolCategory.NONE, ) -> bool:
        # stmt = (
        #     select(cls.model)
        #     .where(
        #         # Если даты в БД хранятся как DateTime, приводим их к Date для точного сравнения дней
        #         func.cast(cls.model.start_date, Date) < end,
        #         func.cast(cls.model.end_date, Date) > start,
        #         cls.model.pool_action == PoolAction.ACTION,
        #         cls.model.pool_category == pool_category
        #     )
        #     .limit(1)
        # )
        stmt = (
            select(cls.model)
            .where(
                cls.model.start_date < end,
                cls.model.end_date > start,
                cls.model.pool_action == PoolAction.ACTION,
                cls.model.pool_category == pool_category
            )
            .limit(1)
        )

        result = await session.execute(stmt)
        pool_instance = result.scalars().first()
        return pool_instance is not None

    @classmethod
    async def get_uuid_action(cls, session: AsyncSession, pool_category: EnumPools) -> str | None:
        stmt = (
            select(Pool.pool_uuid).where(and_(Pool.pool_action == PoolAction.ACTION,
                                              Pool.pool_category == pool_category))
        )
        result = await session.execute(stmt)
        uuid_pool: str | None = result.one_or_none()
        return uuid_pool

    @classmethod
    async def mark_as_deleted(cls, session: AsyncSession, pool_id: int) -> bool:
        stmt = (
            update(cls.model)
            .where(cls.model.id == pool_id)
            .values(pool_action=PoolAction.DELETE, date_update=datetime.now())
            .returning(cls.model.id)
        )
        raw_result: Result = await session.execute(stmt)
        return raw_result.scalar_one_or_none() is not None

    @classmethod
    async def get_object_pool(cls, session: AsyncSession, id_pool: int) -> Pool | None:
        stmt = (select(cls.model)
                .where(cls.model.pool_action == PoolAction.ACTION, cls.model.id == id_pool))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def get_pool_id_by_date_end_now_yesterday(cls, session: AsyncSession,
                                                    pool_category: PoolCategory = PoolCategory.NONE) -> int | None:
        stmt = select(cls.model.id).where(cls.model.pool_action == PoolAction.ACTION,
                                          cls.model.pool_category == pool_category,
                                          cls.model.end_date + timedelta(days=1) == datetime.now().date())
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


class PoolQuestionDAO(BaseDAO[PoolQuestion]):
    model = PoolQuestion

    @classmethod
    async def add_pool_question(cls, session: AsyncSession, data: PoolQuestion) -> PoolQuestion:
        return await cls.add(session=session, data=data)

    @classmethod
    async def get_question_by_id(cls, session: AsyncSession, question_id: int) -> model | None:
        stmt = (
            select(cls.model)
            .options(selectinload(cls.model.poolanswer))
            .where(cls.model.id == question_id)
        )
        return (await session.execute(stmt)).scalar_one_or_none()

    # @staticmethod
    # async def get_object_pool_question_by_pool_id(session: AsyncSession, pool_id: int) -> Sequence[PoolQuestion]:
    #     stmt = select(PoolQuestion).where(PoolQuestion.pool_id == pool_id)
    #     result = await session.execute(stmt)
    #     return result.scalars().all()

    @classmethod
    async def get_object_pool_question_by_pool_id(cls, session: AsyncSession, pool_id: int) -> Sequence[model]:
        stmt = select(cls.model).where(cls.model.pool_id == pool_id)
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_object_pool_question_by_pool_id_and_number_q(session: AsyncSession,
                                                               pool_id: int,
                                                               number_q: int) -> PoolQuestion:
        stmt = select(PoolQuestion).where(
            and_(PoolQuestion.pool_id == pool_id, PoolQuestion.question_number == number_q))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_count_questions(session: AsyncSession, pool_id: int) -> int:
        stmt = select(func.count(PoolQuestion.pool_id)).select_from(PoolQuestion).where(PoolQuestion.pool_id == pool_id)
        result = await session.scalar(stmt)
        return result

    @staticmethod
    async def get_next_question(session: AsyncSession, pool_id: int, current_question_number: int) -> PoolQuestion | None:
        """
        Ищет следующий вопрос в пуле по его порядковому номеру (question_number).
        Возвращает объект PoolQuestion или None, если вопросы закончились.
        """
        stmt = (
            select(PoolQuestion)
            .where(PoolQuestion.pool_id == pool_id)
            .where(PoolQuestion.question_number > current_question_number)
            .order_by(PoolQuestion.question_number.asc())
            # Подгружаем связанные варианты ответов (связь poolanswer),
            # чтобы они сразу были доступны для генерации кнопок в сцене [💡]
            .options(selectinload(PoolQuestion.poolanswer))
            .limit(1)
        )

        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_first_question_of_pool(session: AsyncSession, pool_id: int) -> PoolQuestion | None:
        stmt = (
            select(PoolQuestion)
            .where(PoolQuestion.pool_id == pool_id)
            .order_by(PoolQuestion.question_number.asc())
            .options(selectinload(PoolQuestion.poolanswer))
            .limit(1)
        )

        result = await session.execute(stmt)
        return result.scalar_one_or_none()


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
        return result.scalar_one_or_none()


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

    @classmethod
    async def delete_by_user_and_pool(cls, session: AsyncSession, **kwargs):
        stmt = delete(cls.model).where(and_(cls.model.user_uuid == kwargs["user_uuid"],
                                            cls.model.pool_id == kwargs["pool_id"]))
        await session.execute(stmt)


class UserPoolDAO(BaseDAO[UserPool]):
    model = UserPool

    @classmethod
    async def get_check_survey_completion(cls, session: AsyncSession, **kwargs) -> Result | None:
        # await session.rollback()

        stmt = select(cls.model.end_pool).where(and_(cls.model.user_uuid == kwargs["user_uuid"],
                                                     cls.model.pool_id == kwargs["pool_id"]))
        result = await session.execute(stmt)
        # session.expire_all()
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_user_and_pool(cls, session, user_uuid: str, pool_id: int) -> model | None:
        stmt = select(cls.model).where(
            cls.model.user_uuid == user_uuid, cls.model.pool_id == pool_id,
        )
        return (await session.execute(stmt)).scalar_one_or_none()

    @classmethod
    async def delete_by_user_and_pool(cls, session: AsyncSession, **kwargs):
        stmt = delete(cls.model).where(and_(cls.model.user_uuid == kwargs["user_uuid"],
                                            cls.model.pool_id == kwargs["pool_id"]))
        await session.execute(stmt)


class DAOPools:

    # ---------- приватные: принимают сессию, содержат логику ----------

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

    @staticmethod
    @connection
    async def get_pool_uuid_action(session: AsyncSession, pool_category: PoolCategory) -> str:
        return await PoolDAO.get_uuid_action(session=session, pool_category=pool_category)

    @staticmethod
    @connection
    async def get_pool(session: AsyncSession, **kwargs) -> Pool:
        stmt = (select(Pool).where(and_(Pool.pool_category == kwargs["category"],
                                        Pool.pool_action == PoolAction.ACTION))
                )
        result: Result = await session.execute(stmt)
        # users = await session.scalars(stmt)
        return result.scalar()

    @staticmethod
    async def create_one_record(data: dict) -> bool:
        print(data["question"])
        for i in data["answers"]:
            print(i)
        return False

    @staticmethod
    @connection
    async def get_object_pool_question_by_pool_id(session: AsyncSession, pool_id: int) -> Sequence[PoolQuestion]:
        data = await PoolQuestionDAO.get_object_pool_question_by_pool_id(session=session, pool_id=pool_id)
        return data

    @staticmethod
    @connection
    async def get_answer_by_user_id(session: AsyncSession, **kwargs):
        result = await AnswerDAO.get_answer_by_user_id(session=session, user_uuid=kwargs["user_uuid"])
        return result
