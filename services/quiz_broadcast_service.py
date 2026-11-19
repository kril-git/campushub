import logging
from datetime import date, timedelta

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import bot, settings
from services.EnumQuizStatus import QuizStatus
from services.quiz_report_service import QuizReportService
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
        questions_count = await QuizService.count_questions(quiz_id=quiz.id)  # ← добавить

        text = (
            f"<b>📝 {quiz.title}</b>\n\n"
            f"{quiz.description or ''}\n\n"
            f"Период: {quiz.start_date:%d.%m.%Y} — {quiz.end_date:%d.%m.%Y}\n"
            f"Вопросов: {questions_count}"
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

    @staticmethod
    async def send_all_active() -> dict:
        """Cron 10:00: рассылка по активному квизу (2 группы)."""
        logger.info("QuizBroadcastService.send_all_active: start")
        now = date.today()

        # 1. Все активные
        active = await QuizService.get_all_active(now=now)

        if not active:
            logger.info("send_all_active: нет активных квизов")
            return {"ok": 0, "failed": 0, "errors": []}

        # 2. Если несколько — чиним
        if len(active) > 1:
            logger.warning(
                "send_all_active: найдено %d активных квизов: %s. "
                "Закрываю все, кроме последнего.",
                len(active), [q.id for q in active],
            )
            active_sorted = sorted(active, key=lambda q: q.id, reverse=True)
            latest = active_sorted[0]
            to_close = active_sorted[1:]

            for quiz in to_close:
                await QuizService.finish_quiz(quiz_id=quiz.id)
                logger.info("send_all_active: закрыт квиз id=%s", quiz.id)

            try:
                await bot.send_message(
                    chat_id=settings.MAIN_ADMIN,
                    text=(
                        f"⚠️ <b>Найдено {len(active)} активных квизов</b>\n\n"
                        f"Оставлен последний: <code>{latest.id}</code> ({latest.title})\n"
                        f"Закрыты: {', '.join(str(q.id) for q in to_close)}\n\n"
                        f"Рассылка — по квизу <code>{latest.id}</code>."
                    ),
                    parse_mode="HTML",
                )
            except Exception as e:
                logger.warning("Не удалось отправить отчёт админу: %s", e)

            active = [latest]

        # 3. Рассылка по одному ACTIVE квизу
        quiz = active[0]
        logger.info("send_all_active: рассылка по квизу id=%s", quiz.id)

        # Базовые получатели — с учётом TEST_MODE
        if settings.TEST_MODE:
            all_recipients = list(settings.TEST_USERS)
            logger.info(
                "send_all_active: TEST_MODE=True → TEST_USERS (%d)",
                len(all_recipients),
            )
        else:
            all_recipients = await RecipientsService.get_all_telegram_ids()
            logger.info(
                "send_all_active: TEST_MODE=False → all (%d)",
                len(all_recipients),
            )

        # Фильтр прошедших
        completed = await QuizService.get_completed_user_uuids(quiz_id=quiz.id)

        # Данные по пользователям (для in_progress)
        # users_data = await QuizReportService._get_users_data(quiz_id=quiz.id)
        users_data = await QuizService.get_users_data(quiz_id=quiz.id)
        in_progress = {u["user_uuid"] for u in users_data if not u["end_quiz"]}
        not_started = [
            u for u in all_recipients
            if str(u) not in completed and str(u) not in in_progress
        ]

        logger.info(
            "send_all_active: quiz_id=%s, not_started=%d, in_progress=%d, completed=%d",
            quiz.id, len(not_started), len(in_progress), len(completed),
        )

        # 4. Группа 1 — «Новый квиз»
        result_new = {"ok": 0, "failed": 0, "errors": []}
        if not_started:
            result_new = await QuizBroadcastService._send_new_quiz(
                quiz=quiz, recipients=not_started,
            )

        # 5. Группа 2 — «Продолжить»
        result_continue = {"ok": 0, "failed": 0, "errors": []}
        if in_progress:
            result_continue = await QuizBroadcastService._send_continue_quiz(
                quiz=quiz, recipients=list(in_progress),
            )

        # 6. Итог
        total_ok = result_new["ok"] + result_continue["ok"]
        total_failed = result_new["failed"] + result_continue["failed"]
        total_errors = result_new["errors"] + result_continue["errors"]

        logger.info(
            "send_all_active: quiz_id=%s, ok=%d, failed=%d (new=%d, continue=%d)",
            quiz.id, total_ok, total_failed,
            result_new["ok"], result_continue["ok"],
        )
        return {"ok": total_ok, "failed": total_failed, "errors": total_errors}

    @staticmethod
    async def notify_abandoned() -> dict:
        """Уведомляет бросивших о закрытии квиза (за вчера)."""
        logger.info("QuizBroadcastService.notify_abandoned: start")
        now = date.today()
        yesterday = now - timedelta(days=1)

        abandoned = await QuizService.get_abandoned_after_date(
            after_date=yesterday,
        )

        if not abandoned:
            logger.info("notify_abandoned: нет бросивших за вчера")
            return {"ok": 0, "failed": 0, "errors": []}

        # Фильтр по TEST_MODE
        if settings.TEST_MODE:
            test_set = {str(u) for u in settings.TEST_USERS}
            abandoned = [u for u in abandoned if str(u.user_uuid) in test_set]
            logger.info(
                "notify_abandoned: TEST_MODE=True → после фильтра %d",
                len(abandoned),
            )

        if not abandoned:
            logger.info("notify_abandoned: после фильтра — пусто")
            return {"ok": 0, "failed": 0, "errors": []}

        logger.info("notify_abandoned: найдено %d бросивших", len(abandoned))

        ok = failed = 0
        errors = []

        for quiz_user in abandoned:
            try:
                quiz = await QuizService.get_quiz(quiz_id=quiz_user.quiz_id)
                quiz_title = quiz.title if quiz else "Квиз"

                await bot.send_message(
                    chat_id=quiz_user.user_uuid,
                    text=(
                        f"⏰ <b>Квиз «{quiz_title}» закрыт</b>\n\n"
                        f"Вы не завершили прохождение — ответы обнулены.\n\n"
                        f"Дождитесь следующего квиза."
                    ),
                    parse_mode="HTML",
                )
                ok += 1
            except Exception as e:
                logger.warning(
                    "Не удалось уведомить %s: %s",
                    quiz_user.user_uuid, e,
                )
                failed += 1
                errors.append({
                    "chat_id": quiz_user.user_uuid,
                    "reason": "notify_failed",
                    "error": str(e),
                })

        logger.info(
            "notify_abandoned: ok=%d, failed=%d",
            ok, failed,
        )
        return {"ok": ok, "failed": failed, "errors": errors}

    @staticmethod
    async def _send_new_quiz(quiz, recipients: list[str]) -> dict:
        """Группа 1: «Новый квиз» с кнопками."""
        questions_count = await QuizService.count_questions(quiz_id=quiz.id)  # ← добавить

        kbd = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="✅ Начать / Продолжить",
                callback_data=f"quiz:start:{quiz.id}",
            )],
            [InlineKeyboardButton(
                text="❌ Не сейчас",
                callback_data=f"quiz:decline:{quiz.id}",
            )],
        ])
        text = (
            f"<b>📝 Новый квиз «{quiz.title}»</b>\n\n"
            f"{quiz.description or ''}\n\n"
            f"Период: {quiz.start_date:%d.%m.%Y} — {quiz.end_date:%d.%m.%Y}\n"
            f"Вопросов: {questions_count}"
        )
        ok, failed, errors = await broadcast_text_all_users(
            bot=bot,
            recipients=recipients,
            text=text,
            reply_markup=kbd,
            save_last_message=True,
        )
        return {"ok": ok, "failed": failed, "errors": errors}

    @staticmethod
    async def _send_continue_quiz(quiz, recipients: list[str]) -> dict:
        """Группа 2: «Продолжить N из M» с кнопками."""
        kbd = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="✅ Продолжить",
                callback_data=f"quiz:start:{quiz.id}",
            )],
            [InlineKeyboardButton(
                text="❌ Не сейчас",
                callback_data=f"quiz:decline:{quiz.id}",
            )],
        ])
        text = (
            f"<b>⏰ Вы не завершили квиз «{quiz.title}»</b>\n\n"
            f"Продолжите с места остановки — ответы сохранены."
        )
        ok, failed, errors = await broadcast_text_all_users(
            bot=bot,
            recipients=recipients,
            text=text,
            reply_markup=kbd,
            save_last_message=True,
        )
        return {"ok": ok, "failed": failed, "errors": errors}