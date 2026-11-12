import logging

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import bot, settings
from services.EnumQuizStatus import QuizStatus
from services.quiz_service import QuizService
from services.recipients_services import RecipientsService
from services.sending_service import broadcast_text_all_users

logger = logging.getLogger(__name__)


class QuizBroadcastService:

    @staticmethod
    async def send_quiz(quiz_id: int) -> dict:
        """Ручная рассылка квиза (с учётом TEST_MODE)."""
        logger.info("QuizBroadcastService.send_quiz: quiz_id=%s", quiz_id)

        # 1. Квиз
        quiz = await QuizService.get_quiz(quiz_id=quiz_id)
        if not quiz:
            logger.error("send_quiz: квиз id=%s не найден", quiz_id)
            return {"ok": 0, "failed": 0, "errors": ["Квиз не найден"]}

        if quiz.status != QuizStatus.ACTIVE:
            logger.warning(
                "send_quiz: квиз id=%s не активен (status=%s)",
                quiz_id, quiz.status.value,
            )
            return {"ok": 0, "failed": 0, "errors": ["Квиз не активен"]}

        # 2. Получатели — с учётом TEST_MODE
        if settings.TEST_MODE:
            base_recipients = list(settings.TEST_USERS)
            logger.info(
                "send_quiz: TEST_MODE=True → base TEST_USERS (%d)",
                len(base_recipients),
            )
        else:
            base_recipients = await RecipientsService.get_all_telegram_ids()
            logger.info(
                "send_quiz: TEST_MODE=False → base all (%d)",
                len(base_recipients),
            )

            # Фильтр прошедших
        completed = await QuizService.get_completed_user_uuids(quiz_id=quiz_id)
        recipients = [u for u in base_recipients if str(u) not in completed]

        logger.info(
            "send_quiz: after filter completed (%d) → recipients (%d)",
            len(completed), len(recipients),
        )

        if not recipients:
            logger.info("send_quiz: нет получателей для квиза id=%s", quiz_id)
            return {"ok": 0, "failed": 0, "errors": []}

        # 3. Кнопки
        kbd = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="✅ Начать / Продолжить",
                callback_data=f"quiz:start:{quiz_id}",
            )],
            [InlineKeyboardButton(
                text="❌ Не сейчас",
                callback_data=f"quiz:decline:{quiz_id}",
            )],
        ])

        # 4. Текст
        text = (
            f"<b>📝 {quiz.title}</b>\n\n"
            f"{quiz.description or ''}\n\n"
            f"Период: {quiz.start_date:%d.%m.%Y} — {quiz.end_date:%d.%m.%Y}\n"
            f"Вопросов: {len(quiz.questions)}"
        )

        # 5. Рассылка
        ok, failed, errors = await broadcast_text_all_users(
            bot=bot,
            recipients=recipients,
            text=text,
            reply_markup=kbd,
            save_last_message=True,
        )

        logger.info(
            "send_quiz: quiz_id=%s, ok=%d, failed=%d",
            quiz_id, ok, failed,
        )
        return {"ok": ok, "failed": failed, "errors": errors}