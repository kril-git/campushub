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

router = Router(name=__name__)
logger = logging.getLogger(__name__)


class CompleteSurvey(Scene, state="complete_a_survey"):

    @on.message.enter()
    async def on_enter(self, message: Message, state: FSMContext) -> None:
        pool_id = await DAOPools.get_pool_id_action(pool_category=PoolCategory.NONE)
        if not pool_id:
            await message.answer("Активный опрос не найден.")
            await self.wizard.exit()
            return

        await state.update_data(pool_id=pool_id, answer_list=[], question=0)

        completed: bool = await DAOPools.check_survey_completion(
            pool_id=pool_id, user_uuid=str(message.from_user.id)
        )
        await state.update_data(replay=completed)

        if completed:
            await message.answer(
                "Вы уже проходили данный опрос.\n"
                "Если хотите пройти заново — нажмите 'Начать' 👇",
                reply_markup=r_kb_begin_exit,
            )
        else:
            await message.answer(
                "Мини опрос.\n"
                "Если готовы — нажмите 'Начать', иначе 'Выход' 👇",
                reply_markup=r_kb_begin_exit,
            )

    @on.message(F.text == "👌 Начать")
    async def begin_survey(self, message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        pool_id = data["pool_id"]

        if data.get("replay"):
            await DAOPools.delete_user_pool(
                pool_id=pool_id, user_uuid=str(message.from_user.id)
            )

        await message.answer("Приступим 🕰", reply_markup=r_kb_exit)

        pool = await DAOPools.get_object_pool(id_pool=pool_id)
        count_questions = await DAOPools.get_count_questions(pool_id=pool_id)

        await state.update_data(
            count_questions=count_questions,
            question=0,
            answer_list=[],
        )

        await message.answer(
            # f"Категория {PoolCategory.SALON.name}\n"
            f"Описание {pool.pool_description}\n"
            f"Количество основных вопросов — {count_questions}",
            reply_markup=create_i_kb_begin(pool_id=0, pool_question=0, pool_answer=0),
        )

    @on.callback_query(PoolsCallbackFactory.filter())
    async def get_questions(
        self,
        callback: CallbackQuery,
        callback_data: PoolsCallbackFactory,
        state: FSMContext,
    ) -> None:
        step = 1
        data = await state.get_data()
        pool_id = data["pool_id"]
        question_number = (data.get("question") or 0) + 1
        count_questions = data.get("count_questions") or 0
        # answers: list[Answer] = data.get("answer_list") or []
        answers_list: list[dict] = data.get("answer_list") or []

        await state.update_data(question=question_number)
        await callback.message.edit_reply_markup(reply_markup=None)

        if callback_data.pool_answer != 0:
            answer = await DAOPools.get_object_pool_answer_by_id(
                answer_id=callback_data.pool_answer
            )
            await callback.message.answer(text=f"Ваш ответ 👉 {answer.pool_answer}")
            # answers.append(Answer(
            #     user_uuid=str(callback.from_user.id),
            #     pool_id=callback_data.pool_id,
            #     question_id=callback_data.pool_question,
            #     answer_id=callback_data.pool_answer,
            #     step=step,
            # ))
            answers_list.append({
                "user_uuid": str(callback.from_user.id),
                "pool_id": callback_data.pool_id,
                "question_id": callback_data.pool_question,
                "answer_id": callback_data.pool_answer,
                "step": step,
            })
            await state.update_data(answer_list=answers_list)

        if count_questions < question_number:
            raw = (await state.get_data()).get("answer_list") or []
            answers = [Answer(**a) for a in raw]
            await DAOPools.add_user_answer(data=answers)
            await DAOPools.add_user_pools_record(data=UserPool(
                user_uuid=str(callback.from_user.id),
                pool_id=callback_data.pool_id,
                end_pool=True,
                step=step,
            ))
            await callback.message.answer(
                "Немного передохните и нажмите продолжить 👇",
                reply_markup=i_kb_continue(step=step),
            )
        else:
            pool_question = await DAOPools.get_object_pool_question_by_pool_id_and_number_q(
                pool_id=pool_id, number_q=question_number
            )
            pool_answers = await DAOPools.get_object_pool_answer_by_question_id(
                question_id=pool_question.id
            )
            await callback.message.answer(
                text=f"{pool_question.question_number}. {pool_question.pool_question}",
                reply_markup=create_i_kb_pool_answers(
                    pool_id=pool_id,
                    pool_question=pool_question.id,
                    pool_answers=pool_answers,
                ),
            )

    @on.callback_query(PoolContinueFactory.filter(F.step == 1))
    async def pool_continue(
        self,
        callback: CallbackQuery,
        callback_data: PoolContinueFactory,
        state: FSMContext,
    ) -> None:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer("Переходим к этапу 2.")
        logger.warning("Stage 2 not implemented")

    @on.message(F.text == "🚫 Выход")
    async def exit(self, message: Message, state: FSMContext) -> None:
        await message.answer(
            "Тогда может в следующий раз.",
            reply_markup=ReplyKeyboardRemove(),
        )
        await self.wizard.exit()

    @on.message(Command("cancel"))
    async def cancel(self, message: Message, state: FSMContext) -> None:
        await message.answer("Отменено.", reply_markup=ReplyKeyboardRemove())
        await self.wizard.exit()

    @on.message()
    async def unknown_message(self, message: Message) -> None:
        await message.answer("Пожалуйста, выберите вариант ответа.")


# router.message.register(CompleteSurvey.as_handler(), Command("complete_a_survey"))