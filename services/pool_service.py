import logging
from datetime import datetime

from typing import Any, Sequence

from aiogram.fsm.context import FSMContext
from sqlalchemy import Date
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import connection, readonly

from core.config import settings
from database.dao.pool_dao import DAOPools, PoolDAO, PoolQuestionDAO, PoolAnswerDAO, UserPoolDAO, AnswerDAO
from models.pool import Pool, PoolQuestion, PoolAnswer, Answer, UserPool
# from scenes.load_pool_json_scene import logger
from services.EnumPoolAction import PoolAction
from services.EnumPools import PoolCategory
from services.services import get_timestamp
from utils.text import truncate

logger = logging.getLogger(__name__)


class PoolService:
    @staticmethod
    @connection
    async def create_pool(session: AsyncSession, data: dict) -> int:
        pool: Pool = Pool()
        pool.pool_description = data["pool_description"]
        pool.pool_uuid = get_timestamp()
        pool.pool_category = PoolCategory.get_category(value=data["pool_category"])
        pool.pool_action = PoolAction.ACTION
        pool.is_salute = data["is_salute"]
        pool.start_date = datetime.strptime(data.get("start_date"), "%d.%m.%Y").date()
        pool.end_date = datetime.strptime(data.get("end_date"), "%d.%m.%Y").date()

        pool_record = await PoolDAO.add_pool_record(session=session, data=pool)

        for question in data["questions"]:
            pool_question: PoolQuestion = PoolQuestion()
            pool_question.pool_id = pool_record.id
            pool_question.question_number = question["question_number"]
            pool_question.pool_question = truncate(question["questions"], limit=200)

            pool_question.pool_uuid = pool_record.pool_uuid
            pool_question.pool_question_uuid = get_timestamp()
            pool_question = await PoolQuestionDAO.add(session=session, data=pool_question)
            uuid_answer = get_timestamp()
            answers = []
            for i, answer in enumerate(question["answers"], start=1):
                pool_answer: PoolAnswer = PoolAnswer()
                pool_answer.pool_question_id = pool_question.id
                pool_answer.pool_answer_uuid = uuid_answer
                pool_answer.pool_question_uuid = pool_question.pool_question_uuid
                pool_answer.answer_number = i
                pool_answer.pool_answer = answer
                answers.append(pool_answer)
            await PoolAnswerDAO.add_many(session=session, data=answers)
        return pool_record.id

    @staticmethod
    @readonly
    async def get_active_pool_id(session: AsyncSession, pool_category: PoolCategory = PoolCategory.NONE) -> int | None:
        return await PoolDAO.get_id_action(session, pool_category)

    @staticmethod
    @readonly
    async def has_intersecting_pool(session: AsyncSession, start: Date, end: Date) -> bool:
        return await PoolDAO.has_intersecting_pool(session=session, start=start, end=end)

    @staticmethod
    @readonly
    async def get_active_pool_end_date_yesterday(session: AsyncSession, pool_category: PoolCategory) -> datetime | None:
        return await PoolDAO.get_pool_id_by_date_end_now_yesterday(session, pool_category)

    @staticmethod
    @readonly
    async def check_survey_completion(session: AsyncSession, **kwargs) -> bool:
        """
           Вернет False если пользователь не проходил опрос или значение в БД равно False
           """
        res = await UserPoolDAO.get_check_survey_completion(session=session, **kwargs)

        # Если записи нет (None) или в столбце записано False — возвращаем False (пользователь может проходить)
        if res is None or res is False:
            return False

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
    @readonly
    async def get_object_pool(session: AsyncSession, id_pool: int) -> Pool:
        data = await PoolDAO.get_object_pool(session=session, id_pool=id_pool)
        return data

    @staticmethod
    @readonly
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
    async def finish_survey(
            session: AsyncSession,
            answers: list[Answer],
            user_pool: UserPool,
    ) -> None:
        await AnswerDAO.add_many(session, answers)
        await UserPoolDAO.add(session, user_pool)
        # commit сделает @connection — один на всё

    @staticmethod
    @connection
    async def mark_as_deleted_pool(session: AsyncSession, pool_id: int) -> bool:
        return await PoolDAO.mark_as_deleted(session=session, pool_id=pool_id)

    @staticmethod
    @readonly
    async def get_object_pool_question_by_pool_id(session: AsyncSession, pool_id: int) -> Sequence[PoolQuestion]:
        return await PoolQuestionDAO.get_object_pool_question_by_pool_id(session=session, pool_id=pool_id)

    @staticmethod
    @readonly
    async def get_object_pool_answer_by_question_id(session: AsyncSession, question_id: int) -> Sequence[PoolQuestion]:
        return await PoolAnswerDAO.get_object_pool_answer_by_question_id(session=session, question_id=question_id)


async def get_info_pool(pool_id: int) -> str:
    pool = await PoolService.get_object_pool(id_pool=pool_id)
    list_info = [f"Название опроса: {pool.pool_description}\n",
                 f"Категория: {pool.pool_category.name}\n",
                 f"Дата начала: {pool.start_date}\n",
                 f"Дата окончания: {pool.end_date}\n",
                 f"------------------\n\n"
                 ]

    questions = await PoolService.get_object_pool_question_by_pool_id(pool_id=pool.id)
    for item in questions:
        list_info.append(f"   {item.question_number}. {item.pool_question}\n")
        answers = await PoolService.get_object_pool_answer_by_question_id(question_id=item.id)
        for answer in answers:
            list_info.append(f"{answer.pool_answer}\n")
        list_info.append(f"----------\n")
    return "".join(list_info)
