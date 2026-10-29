# database/dao/report_dao.py
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import readonly
from database.dao.base import BaseDAO
from models import Answer, PersonalRecordCard, PoolQuestion, PoolAnswer, UserPool


class ReportDAO(BaseDAO[Answer]):
    model = Answer

    @staticmethod
    @readonly
    async def get_answers_with_users(session: AsyncSession, pool_id: int) -> list[dict]:
        """
        Плоский вид: все ответы по пулу + ФИО + группа (запрос 2а).
        """
        stmt = (
            select(
                Answer.user_uuid.label("uuid"),
                Answer.step,
                PoolQuestion.question_number,
                PoolQuestion.pool_question,
                PoolAnswer.answer_number,
                PoolAnswer.pool_answer,
                PersonalRecordCard.surname,
                PersonalRecordCard.given_name,
                PersonalRecordCard.middle_name,
                PersonalRecordCard.group,
            )
            .join(PersonalRecordCard, PersonalRecordCard.uuid == Answer.user_uuid, isouter=True)
            .join(PoolQuestion, PoolQuestion.id == Answer.question_id)
            .join(PoolAnswer, PoolAnswer.id == Answer.answer_id)
            .where(Answer.pool_id == pool_id)
            .order_by(Answer.user_uuid, PoolQuestion.question_number)
        )
        result = await session.execute(stmt)
        return [dict(row._mapping) for row in result.all()]

    @staticmethod
    @readonly
    async def get_all_users_with_info(session: AsyncSession) -> list[dict]:
        """Все зарегистрированные (uuid, ФИО, группа, телефон, email)."""
        stmt = select(
            PersonalRecordCard.uuid,
            PersonalRecordCard.surname,
            PersonalRecordCard.given_name,
            PersonalRecordCard.middle_name,
            PersonalRecordCard.group,
            PersonalRecordCard.phone,
            PersonalRecordCard.email,
        )
        result = await session.execute(stmt)
        return [dict(row._mapping) for row in result.all()]

    @staticmethod
    @readonly
    async def get_completion_status(session: AsyncSession, pool_id: int) -> list[dict]:
        """Статус прохождения: uuid, end_pool, step, date_update."""
        stmt = (
            select(
                PersonalRecordCard.uuid,
                UserPool.end_pool,
                UserPool.step,
                UserPool.date_update,
            )
            .join(UserPool, and_(
                UserPool.user_uuid == PersonalRecordCard.uuid,
                UserPool.pool_id == pool_id,
            ), isouter=True)
        )
        result = await session.execute(stmt)
        return [dict(row._mapping) for row in result.all()]