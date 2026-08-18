import logging

from aiogram import Router, F, flags
from aiogram.enums import ChatAction, ContentType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import Scene, on
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery

from database.dao.pool_repository import DAOPools
from keyboards.callback_data_factory import PoolsCallbackFactory, PoolContinueFactory
from keyboards.inline_keyboard import create_i_kb_begin, create_i_kb_pool_answers, i_kb_continue
from keyboards.reply_keyboar import r_kb_exit, r_kb_begin_exit
from models import Answer, UserPool
from services.EnumPools import PoolCategory
from services.pool_services import get_data_from_json, create_pool, get_info_pool

router = Router(name=__name__)
logger = logging.getLogger(__name__)


class CompleteSurvey(Scene, state="complete_a_survey"):
    answer_list: list[Answer] = []

    @on.message.enter()
    @flags.chat_action(action=ChatAction.TYPING)
    async def on_enter(self, message: Message, state: FSMContext):
        pool_id = await DAOPools.get_pool_id_action(pool_category=PoolCategory.SALON)
        await state.update_data(pool_id=pool_id)
        if DAOPools.check_survey_completion(pool_id=pool_id, user_uuid=str(message.from_user.id)):
            await message.answer(text=f"Вы уже проходили данный опрос\n"
                                      f"Если хотите пройти заново"
                                      f"нажмите кнопку 'Начать'"
                                      f"👇",
                                 reply_markup=r_kb_begin_exit)
            await state.update_data(replay=True)

        else:
            await message.answer(text=f"Мини опрос\n"
                                      f"Если Вы готовы, нажмите кнопку 'Начать', иначе выберите 'Выход'\n"
                                      f"👇",
                                 reply_markup=r_kb_begin_exit)
            await state.update_data(replay=False)

    @on.message(F.text.contains("Начать"))
    @flags.chat_action(action=ChatAction.TYPING)
    async def begin_survey(self, message: Message, state: FSMContext):
        data = await state.get_data()
        if data.get("replay"):
            await DAOPools.delete_user_pool(pool_id=data.get("pool_id"), user_uuid=str(message.from_user.id))
            pass
        await message.answer(text="Приступим 🕰", reply_markup=r_kb_exit)
        pool = await DAOPools.get_object_pool(id_pool=data.get("pool_id"))
        count_questions = await DAOPools.get_count_questions(pool_id=data.get("pool_id"))
        await state.update_data(count_questions=count_questions)
        await state.update_data(question=0)
        await message.answer(text=f"Категория {PoolCategory.SALON.name}\n"
                                  f"Описание {pool.pool_description}\n"
                                  f"Количество основных вопросов -  {count_questions}",
                             reply_markup=create_i_kb_begin(pool_id=0,
                                                            pool_question=0,
                                                            pool_answer=0))

    @on.callback_query(PoolsCallbackFactory.filter())
    @flags.chat_action(action=ChatAction.TYPING)
    async def get_questions(self, callback: CallbackQuery, callback_data: PoolsCallbackFactory, state: FSMContext):
        step: int = 1
        data = await state.get_data()
        question_number = data.get("question")
        count_questions = data.get("count_questions")
        question_number += 1
        await state.update_data(question=question_number)
        await callback.message.edit_reply_markup(reply_markup=None)
        answer = await DAOPools.get_object_pool_answer_by_id(answer_id=callback_data.pool_answer)
        if callback_data.pool_answer != 0:
            await callback.message.answer(text=f"Ваш ответ 👉 {answer.pool_answer}")
            self.answer_list.append(Answer(
                user_uuid=str(callback.from_user.id),
                pool_id=callback_data.pool_id,
                question_id=callback_data.pool_question,
                answer_id=callback_data.pool_answer,
                step=step)
            )
        if count_questions < question_number:
            await DAOPools.add_user_answer(data=self.answer_list)
            await DAOPools.add_user_pools_record(data=UserPool(
                user_uuid=str(callback.from_user.id),
                pool_id=callback_data.pool_id,
                end_pool=True,
                step=step)
            )
            await callback.message.answer(text=f"Немного передохните и нажмите продолжить. 👇",
                                          reply_markup=i_kb_continue(step=step))
        else:
            pool_question = await DAOPools.get_object_pool_question_by_pool_id_and_number_q(pool_id=data.get("pool_id"),
                                                                                            number_q=question_number)
            pool_answers = await DAOPools.get_object_pool_answer_by_question_id(question_id=pool_question.id)
            await callback.message.answer(
                text=f"{pool_question.question_number}. {pool_question.pool_question}",
                reply_markup=create_i_kb_pool_answers(pool_id=data.get("pool_id"),
                                                      pool_question=pool_question.id,
                                                      pool_answers=pool_answers))

    @on.callback_query(PoolContinueFactory.filter(F.step == 1))
    async def pool_continue(self, callback: CallbackQuery, callback_data: PoolContinueFactory, state: FSMContext):
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(text=f"Переходим к этапу 2.")

    @on.message(F.content_type == ContentType.DOCUMENT)
    @flags.chat_action(action=ChatAction.UPLOAD_DOCUMENT)
    async def load_json(self, message: Message, state: FSMContext):
        if message.document.mime_type == "application/json":
            data = await get_data_from_json(message)
            if data:
                try:
                    id_pool = await create_pool(data=data, state=state)
                    await message.answer(text=await get_info_pool(pool_id=id_pool), reply_markup=ReplyKeyboardRemove())
                    await message.answer(text=f"Если что то не корректно, отредактируйте JSON-файл и повторите "
                                              f"действия.\n"
                                              f" /json_pool_load")
                except Exception as e:
                    logger.error(f"{e}")
                    await message.answer(text=f"Что то так")
                    raise e
            else:
                await message.answer("Убедитесь в пароле и загрузите файл повторно.\n"
                                     "Жду файл 🕰")
                logger.error("Пароль в файле не соответствует")
        else:
            await message.answer(f"Я ожидаю JSON файл.")

    @on.message(F.text.contains("Выход"))
    async def exit(self, message: Message, state: FSMContext) -> None:
        await message.answer(text="Тогда может в следующий раз.", reply_markup=ReplyKeyboardRemove())
        await self.wizard.exit()

    @on.message()
    async def unknown_message(self, message: Message) -> None:
        """
        Method triggered when the user sends a message that is not a command or an answer.

        It asks the user to select an answer.

        :param message: The message received from the user.
        :return: None
        """
        await message.answer("Please select an answer.")


router.message.register(CompleteSurvey.as_handler(), Command("complete_a_survey"))
