import logging
from datetime import date, datetime

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.dao.base import BaseDAO
from models import (
    Quiz, QuizQuestion, QuizAnswer, QuizResponse, QuizUser,
)
from services.EnumQuizStatus import QuizStatus

logger = logging.getLogger(__name__)


# ==================== QuizDAO ====================

class QuizDAO(BaseDAO[Quiz]):
    model = Quiz

    @classmethod
    async def get_with_questions(cls, session: AsyncSession, quiz_id: int) -> Quiz | None:
        """Квиз с вопросами и ответами (selectinload)."""
        stmt = (
            select(cls.model)
            .options(
                selectinload(cls.model.questions)
                .selectinload(QuizQuestion.answers)
            )
            .where(cls.model.id == quiz_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def get_active(cls, session: AsyncSession, now: date | None = None) -> Quiz | None:
        """Активный квиз на сейчас (status=ACTIVE + даты)."""
        if now is None:
            now = date.today()
        stmt = (
            select(cls.model)
            .where(
                cls.model.status == QuizStatus.ACTIVE,
                cls.model.start_date <= now,
                cls.model.end_date >= now,
            )
            .order_by(cls.model.id.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def get_active_with_questions(cls, session: AsyncSession, now: date | None = None) -> Quiz | None:
        """Активный квиз с вопросами и ответами."""
        if now is None:
            now = date.today()
        stmt = (
            select(cls.model)
            .options(
                selectinload(cls.model.questions)
                .selectinload(QuizQuestion.answers)
            )
            .where(
                cls.model.status == QuizStatus.ACTIVE,
                cls.model.start_date <= now,
                cls.model.end_date >= now,
            )
            .order_by(cls.model.id.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def get_all_active(cls, session: AsyncSession, now: date | None = None) -> list[Quiz]:
        """Все активные квизы на сейчас."""
        if now is None:
            now = date.today()
        stmt = (
            select(cls.model)
            .where(
                cls.model.status == QuizStatus.ACTIVE,
                cls.model.start_date <= now,
                cls.model.end_date >= now,
            )
            .order_by(cls.model.id.desc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def get_recent(cls, session: AsyncSession, limit: int = 5) -> list[Quiz]:
        """Последние N квизов (для админки)."""
        stmt = (
            select(cls.model)
            .order_by(cls.model.id.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def set_status(cls, session: AsyncSession, quiz_id: int, status: QuizStatus) -> None:
        """Сменить статус квиза."""
        stmt = (
            update(cls.model)
            .where(cls.model.id == quiz_id)
            .values(status=status)
        )
        await session.execute(stmt)

    @classmethod
    async def get_finished_before(cls, session: AsyncSession, before_date: date) -> list[Quiz]:
        """Квизы, у которых end_date < before_date (для чистки)."""
        stmt = (
            select(cls.model)
            .where(cls.model.end_date < before_date)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def get_conflicting(
        cls,
        session: AsyncSession,
        start_date: date,
        end_date: date,
        exclude_quiz_id: int | None = None,
    ) -> Quiz | None:
        """Первый квиз с пересечением дат (DRAFT/ACTIVE)."""
        stmt = (
            select(cls.model)
            .where(
                cls.model.status.in_([QuizStatus.DRAFT, QuizStatus.ACTIVE]),
                cls.model.start_date <= end_date,
                cls.model.end_date >= start_date,
            )
        )
        if exclude_quiz_id is not None:
            stmt = stmt.where(cls.model.id != exclude_quiz_id)

        result = await session.execute(stmt)
        return result.scalars().first()


# ==================== QuizQuestionDAO ====================

class QuizQuestionDAO(BaseDAO[QuizQuestion]):
    model = QuizQuestion

    @classmethod
    async def get_by_quiz(cls, session: AsyncSession, quiz_id: int) -> list[QuizQuestion]:
        """Все вопросы квиза (по порядку)."""
        stmt = (
            select(cls.model)
            .where(cls.model.quiz_id == quiz_id)
            .order_by(cls.model.number)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def get_by_quiz_with_answers(
        cls, session: AsyncSession, quiz_id: int,
    ) -> list[QuizQuestion]:
        """Все вопросы квиза с ответами (selectinload)."""
        stmt = (
            select(cls.model)
            .options(selectinload(QuizQuestion.answers))
            .where(cls.model.quiz_id == quiz_id)
            .order_by(cls.model.number)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def get_by_quiz_and_after_number(
        cls, session: AsyncSession, quiz_id: int, after_number: int,
    ) -> QuizQuestion | None:
        """Следующий вопрос (number > after_number) с ответами."""
        stmt = (
            select(cls.model)
            .options(selectinload(QuizQuestion.answers))
            .where(
                cls.model.quiz_id == quiz_id,
                cls.model.number > after_number,
            )
            .order_by(cls.model.number)
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_quiz_and_number(
        cls, session: AsyncSession, quiz_id: int, number: int,
    ) -> QuizQuestion | None:
        """Вопрос по номеру."""
        stmt = (
            select(cls.model)
            .where(
                cls.model.quiz_id == quiz_id,
                cls.model.number == number,
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def count_by_quiz(cls, session: AsyncSession, quiz_id: int) -> int:
        """Количество вопросов в квизе."""
        stmt = (
            select(func.count())
            .select_from(cls.model)
            .where(cls.model.quiz_id == quiz_id)
        )
        return (await session.scalar(stmt)) or 0

    @classmethod
    async def get_first(cls, session: AsyncSession, quiz_id: int) -> QuizQuestion | None:
        """Первый вопрос квиза с ответами."""
        return await cls.get_by_quiz_and_after_number(
            session=session, quiz_id=quiz_id, after_number=0,
        )


# ==================== QuizAnswerDAO ====================

class QuizAnswerDAO(BaseDAO[QuizAnswer]):
    model = QuizAnswer

    @classmethod
    async def get_by_question(cls, session: AsyncSession, question_id: int) -> list[QuizAnswer]:
        """Все ответы на вопрос (по порядку)."""
        stmt = (
            select(cls.model)
            .where(cls.model.question_id == question_id)
            .order_by(cls.model.number)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def get_correct(cls, session: AsyncSession, question_id: int) -> QuizAnswer | None:
        """Правильный ответ на вопрос."""
        stmt = (
            select(cls.model)
            .where(
                cls.model.question_id == question_id,
                cls.model.is_correct.is_(True),
            )
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


# ==================== QuizResponseDAO ====================

class QuizResponseDAO(BaseDAO[QuizResponse]):
    model = QuizResponse

    @classmethod
    async def get_by_user_and_quiz(
        cls, session: AsyncSession, user_uuid: str, quiz_id: int,
    ) -> list[QuizResponse]:
        """Все ответы пользователя на квиз (по порядку шагов)."""
        stmt = (
            select(cls.model)
            .where(
                cls.model.user_uuid == user_uuid,
                cls.model.quiz_id == quiz_id,
            )
            .order_by(cls.model.step)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def get_correct_count(
        cls, session: AsyncSession, user_uuid: str, quiz_id: int,
    ) -> int:
        """Количество правильных ответов пользователя."""
        stmt = (
            select(func.count())
            .select_from(cls.model)
            .where(
                cls.model.user_uuid == user_uuid,
                cls.model.quiz_id == quiz_id,
                cls.model.is_correct.is_(True),
            )
        )
        return (await session.scalar(stmt)) or 0


# ==================== QuizUserDAO ====================

class QuizUserDAO(BaseDAO[QuizUser]):
    model = QuizUser

    @classmethod
    async def get_by_user_and_quiz(
        cls, session: AsyncSession, user_uuid: str, quiz_id: int,
    ) -> QuizUser | None:
        """Прохождение квиза пользователем."""
        stmt = (
            select(cls.model)
            .where(
                cls.model.user_uuid == user_uuid,
                cls.model.quiz_id == quiz_id,
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def get_completed_user_uuids(
        cls, session: AsyncSession, quiz_id: int,
    ) -> set[str]:
        """Множество user_uuid, кто завершил квиз (end_quiz=True)."""
        stmt = (
            select(cls.model.user_uuid)
            .where(
                cls.model.quiz_id == quiz_id,
                cls.model.end_quiz.is_(True),
            )
        )
        result = await session.execute(stmt)
        return {row[0] for row in result.all()}

    @classmethod
    async def get_abandoned(
        cls, session: AsyncSession, before_date: date,
    ) -> list[QuizUser]:
        """Брошенные прохождения (end_quiz=False, квиз закончился)."""
        stmt = (
            select(cls.model)
            .join(Quiz, Quiz.id == cls.model.quiz_id)
            .where(
                cls.model.end_quiz.is_(False),
                Quiz.end_date < before_date,
            )
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())