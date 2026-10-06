import logging
from datetime import datetime

from typing import Any

from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import connection

from core.config import settings
from database.dao.pool_dao import DAOPools, PoolDAO, PoolQuestionDAO, PoolAnswerDAO
from models.pool import Pool, PoolQuestion, PoolAnswer
# from scenes.load_pool_json_scene import logger
from services.EnumPoolAction import PoolAction
from services.EnumPools import PoolCategory
from services.services import get_timestamp
from utils.text import truncate

logger = logging.getLogger(__name__)


# def get_passwords() -> list:
#     return settings.PASSWORDS.split(",")
#
#
# async def create_pool_data():
#     pass


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


async def get_info_pool(pool_id: int) -> str:
    pool = await DAOPools.get_object_pool(id_pool=pool_id)
    list_info = [f"Название опроса: {pool.pool_description}\n", f"Категория: {pool.pool_category.name}\n\n"]

    questions = await DAOPools.get_object_pool_question_by_pool_id(pool_id=pool.id)
    for item in questions:
        list_info.append(f"   {item.question_number}. {item.pool_question}\n")
        answers = await DAOPools.get_object_pool_answer_by_question_id(question_id=item.id)
        for answer in answers:
            list_info.append(f"{answer.pool_answer}\n")
        list_info.append(f"----------\n")
    return "".join(list_info)
