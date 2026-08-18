import json
import logging

from typing import Any

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from core.config import settings
from database.dao.pool_repository import DAOPools
from models import Pool, PoolQuestion, PoolAnswer
# from scenes.load_pool_json_scene import logger
from services.EnumPoolAction import PoolAction
from services.EnumPools import PoolCategory
from services.services import get_timestamp

logger = logging.getLogger(__name__)


def get_passwords() -> list:
    return settings.PASSWORDS.split(",")


async def get_data_from_json(message: Message) -> Any:
    await message.answer(f"Отлично, я получил нужный документ.\n <i>Проверяю его корректность.</i>")
    try:
        file_info = await message.bot.get_file(message.document.file_id)
        downloaded_file = await message.bot.download_file(file_info.file_path)
        downloaded_file.seek(0)
        data = json.load(downloaded_file)
    except Exception as e:
        logger.error("Проблема структуры файла")
        await message.answer(text=f"Проблема структуры файла.\n"
                                  f"Нажмите выход, проверьте файл\n"
                                  f"и начните заново. /json_pool_load")
        raise e

    if data["password"] in get_passwords():
        await message.answer(text=f"👍 Проверка прошла успешно!\n"
                                  f"Ожидайте, сохраняю информацию в базе данных\n"
                                  f"После завершения отправлю информацию для проверки.\n"
                                  f"🎯")
        return data
    else:
        await message.answer(text="👎 Пароль в файле не совпадает с контрольным")
        return None


async def create_pool_data():
    pass


async def create_pool(data: Any, state: FSMContext) -> int:
    pool_data: dict = {}
    logger.info("Пароль в файле соответствует действующему.")
    pool = Pool()
    pool.pool_description = data["pool_description"]
    pool.pool_uuid = get_timestamp()
    pool.pool_category = PoolCategory.get_category(value=data["pool_category"])
    pool.pool_action = PoolAction.ACTION

    pool_record = await DAOPools.add_pool_record(data=pool)

    for question in data["questions"]:
        pool_data.clear()
        pool_question: PoolQuestion = PoolQuestion()
        pool_question.pool_id = pool_record.id
        pool_question.question_number = question["question_number"]
        if len(question["questions"]) > 200:
            pool_question.pool_question = question["questions"][:199]
        else:
            pool_question.pool_question = question["questions"]
        pool_question.pool_uuid = pool.pool_uuid
        pool_question.pool_question_uuid = get_timestamp()
        try:
            pool_question = await DAOPools.add_pool_question(data=pool_question)
        except Exception as e:
            logger.error(f"ERROR {e}")
            raise e
        uuid_answer = get_timestamp()
        count = 1
        pool_data["question"] = pool_question
        answers = []
        for answer in question["answers"]:
            pool_answer: PoolAnswer = PoolAnswer()
            pool_answer.pool_question_id = pool_question.id
            pool_answer.pool_answer_uuid = uuid_answer
            pool_answer.pool_question_uuid = pool_question.pool_question_uuid
            pool_answer.answer_number = count
            pool_answer.pool_answer = answer
            count = count + 1
            answers.append(pool_answer)
        pool_data["answers"] = answers
        await DAOPools.add_pool_answer(data=answers)
    await state.clear()
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
