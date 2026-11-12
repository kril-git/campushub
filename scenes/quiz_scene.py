import logging

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import Scene, on
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
)

from config import bot, settings
from services.quiz_service import QuizService

logger = logging.getLogger(__name__)


class QuizScene(Scene, state="quiz"):
    """Сцена прохождения квиза."""

    # ==================== Вход ====================

    @on.callback_query.enter()
    async def on_enter(self, callback: CallbackQuery, state: FSMContext):
        """Вход по кнопке «Начать / Продолжить»."""
        await callback.answer()

        # quiz_id из callback_data: "quiz:start:<quiz_id>"
        parts = callback.data.split(":")
        if len(parts) < 3:
            await callback.message.answer("❌ Неверный формат кнопки")
            await self.wizard.exit()
            return

        try:
            quiz_id = int(parts[2])
        except ValueError:
            await callback.message.answer("❌ Неверный ID квиза")
            await self.wizard.exit()
            return

        user_uuid = str(callback.from_user.id)

        # Сохраняем в state
        await state.update_data(quiz_id=quiz_id, user_uuid=user_uuid)

        # Проверяем, не завершён ли уже
        quiz_user = await QuizService.get_user(
            user_uuid=user_uuid, quiz_id=quiz_id,
        )
        if quiz_user and quiz_user.end_quiz:
            await callback.message.answer(
                "✅ Вы уже прошли этот квиз.\n"
                f"Ваш результат: {quiz_user.correct_count} из {quiz_user.total_count}."
            )
            await state.clear()
            await self.wizard.exit()
            return

        # Показываем первый вопрос (или продолжаем)
        await self._show_next_question(callback.message, state)

    # ==================== Ответ ====================

    @on.callback_query(F.data.startswith("quiz:answer:"))
    async def on_answer(self, callback: CallbackQuery, state: FSMContext):
        await callback.answer()

        # data: "quiz:answer:<question_id>:<answer_id>"
        parts = callback.data.split(":")
        if len(parts) < 4:
            return

        try:
            question_id = int(parts[2])
            answer_id = int(parts[3])
        except ValueError:
            return

        data = await state.get_data()
        quiz_id = data.get("quiz_id")
        user_uuid = data.get("user_uuid")

        if not quiz_id or not user_uuid:
            await callback.message.answer("❌ Ошибка: нет данных квиза")
            await self.wizard.exit()
            return

        # Сохраняем ответ
        try:
            result = await QuizService.save_answer(
                user_uuid=user_uuid,
                quiz_id=quiz_id,
                question_id=question_id,
                answer_id=answer_id,
            )
        except Exception as e:
            logger.exception("Ошибка save_answer: %s", e)
            await callback.message.answer(f"❌ Ошибка: {e}")
            await self.wizard.exit()
            return

        # Показываем правильный / неправильный
        if result["is_correct"]:
            feedback = "✅ Верно!"
        else:
            feedback = (
                f"❌ Неверно.\n"
                f"Правильный ответ: «{result['correct_text']}»"
            )
            if result["comment"]:
                feedback += f"\n\n💡 {result['comment']}"

        await callback.message.answer(feedback)

        # Следующий вопрос
        await self._show_next_question(callback.message, state)

    # ==================== Показ вопроса / итог ====================

    async def _show_next_question(self, message: Message, state: FSMContext):
        """Показать следующий вопрос или итог."""
        data = await state.get_data()
        quiz_id = data.get("quiz_id")
        user_uuid = data.get("user_uuid")

        if not quiz_id or not user_uuid:
            await self.wizard.exit()
            return

        next_question = await QuizService.get_next_question(
            user_uuid=user_uuid, quiz_id=quiz_id,
        )

        if next_question is None:
            # Итог
            await self._show_result(message, state)
            return

        # Показываем вопрос
        await self._show_question(message, state, next_question)

    async def _show_question(self, message: Message, state: FSMContext, question):
        """Показать вопрос с кнопками ответов."""
        data = await state.get_data()
        quiz_id = data.get("quiz_id")

        if not question.answers:
            await message.answer("❌ У вопроса нет ответов")
            await self.wizard.exit()
            return

        # Кнопки ответов
        buttons = [
            [InlineKeyboardButton(
                text=a.text,
                callback_data=f"quiz:answer:{question.id}:{a.id}",
            )]
            for a in question.answers
        ]
        kbd = InlineKeyboardMarkup(inline_keyboard=buttons)

        # Номер вопроса — из state
        current = (await state.get_data()).get("current_number", 1)
        await state.update_data(current_number=current + 1)

        await message.answer(
            f"<b>Вопрос {current}:</b>\n\n{question.text}",
            parse_mode="HTML",
            reply_markup=kbd,
        )

    async def _show_result(self, message: Message, state: FSMContext):
        """Показать итог."""
        data = await state.get_data()
        quiz_id = data.get("quiz_id")
        user_uuid = data.get("user_uuid")

        quiz_user = await QuizService.get_user(
            user_uuid=user_uuid, quiz_id=quiz_id,
        )

        if quiz_user:
            await message.answer(
                f"🎉 <b>Квиз завершён!</b>\n\n"
                f"Вы ответили на {quiz_user.correct_count} из {quiz_user.total_count} правильно.\n\n"
                f"Спасибо за прохождение!",
                parse_mode="HTML",
            )
        else:
            await message.answer("✅ Квиз завершён.")

        await state.clear()
        await self.wizard.exit()