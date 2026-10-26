import logging

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import Scene, on
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from keyboards.inline_keyboard import generate_inline_keyboard_for_question
from models import Answer, UserPool
from services.pool_service import PoolService

logger = logging.getLogger(__name__)


class DirectSurveyScene(Scene, state="direct_survey_scene"):
    """Сцена для последовательного прохождения опросов."""

    @on.callback_query.enter()
    async def on_enter(self, event: Message | CallbackQuery, state: FSMContext):
        """АВТОМАТИЧЕСКИ при scenes.enter(...)."""
        logger.info("🔥 ON_ENTER CALLED: %s", type(event).__name__)
        message = event if isinstance(event, Message) else event.message
        await self.show_step(message, state)

    @on.callback_query(F.data.startswith("survey_ans:"))
    async def process_answer(self, callback: CallbackQuery, state: FSMContext):
        await callback.answer()

        _, pool_id, q_num, ans_id = callback.data.split(":")
        pool_id, q_num, ans_id = int(pool_id), int(q_num), int(ans_id)

        try:
            await callback.message.delete()
        except Exception:
            pass

        data = await state.get_data()
        user_data = data.get("user_data", {})
        answers_list = user_data.get("answers_list", [])
        step = user_data.get("step", 0)
        current_qid = user_data.get("current_question_id")

        answers_list.append({
            "user_uuid": str(callback.from_user.id),
            "pool_id": pool_id,
            "question_id": current_qid,
            "answer_id": ans_id,
            "step": step,
        })

        next_question = await PoolService.get_next_question(
            pool_id=pool_id,
            current_question_number=q_num,
        )
        logger.info("process_answer: next_question=%s", next_question)

        if next_question:
            user_data.update({
                "answers_list": answers_list,
                "step": step + 1,
                "current_question_id": next_question.id,
            })
            await state.update_data(user_data=user_data)
            await self.show_step(callback.message, state)
        else:
            await callback.message.answer("⏳ Сохраняю ваши ответы...")
            await PoolService.finish_survey(
                answers=[Answer(**a) for a in answers_list],
                user_pool=UserPool(
                    user_uuid=str(callback.from_user.id),
                    pool_id=pool_id,
                    end_pool=True,
                    step=step,
                ),
            )
            await callback.message.answer(
                "🎉 Спасибо! Вы успешно прошли опрос.",
                reply_markup=ReplyKeyboardRemove(),
            )
            await state.clear()
            await self.wizard.exit()

    async def show_step(self, message: Message, state: FSMContext):
        data = await state.get_data()
        user_data = data.get("user_data", {})
        question_id = user_data.get("current_question_id")
        pool_id = user_data.get("pool_id")
        logger.info(
            "show_step: question_id=%s, pool_id=%s, state=%s",
            question_id, pool_id, user_data,
        )

        if not question_id:
            await message.answer("Сессия истекла. Начните опрос заново.")
            await state.clear()
            await self.wizard.exit()
            return

        question = await PoolService.get_question_by_id(question_id=question_id)
        if not question:
            await message.answer("Вопрос не найден.")
            await state.clear()
            await self.wizard.exit()
            return

        kbd = generate_inline_keyboard_for_question(
            buttons=question.poolanswer,
            prefix=f"survey_ans:{pool_id}:{question.question_number}",
        )
        await message.answer(
            text=f"<b>Вопрос №{question.question_number}:</b>\n{question.pool_question}",
            reply_markup=kbd,
        )