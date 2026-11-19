import logging
from io import BytesIO
from datetime import datetime, date

import pandas as pd
from aiogram.types import BufferedInputFile

from config import bot, settings
from database.db_helper import db_helper
from database.dao.report_dao import ReportDAO
from services.quiz_service import QuizService

logger = logging.getLogger(__name__)


class QuizReportService:
    """Генерация Excel-отчёта по квизу (3 вкладки)."""

    # ==================== Публичные ====================

    @staticmethod
    async def build_quiz_report(quiz_id: int) -> BytesIO:
        """Excel-отчёт в памяти."""
        # 1. Квиз
        quiz = await QuizService.get_quiz(quiz_id=quiz_id)
        if not quiz:
            raise ValueError(f"Квиз {quiz_id} не найден")

        max_q = await QuizService.count_questions(quiz_id=quiz_id)  # ← через сервис

        if max_q == 0:
            raise ValueError(f"У квиза {quiz_id} нет вопросов")

        # 2. Данные
        answers_data = await QuizReportService._get_answers_data(quiz_id=quiz_id)
        users_data = await QuizReportService._get_users_data(quiz_id=quiz_id)
        all_users = await ReportDAO.get_all_users_with_info()

        # 3. DataFrame'ы
        df_summary = QuizReportService._build_summary_df(quiz, answers_data, users_data)
        df_details = QuizReportService._build_details_df(
            quiz, answers_data, users_data, all_users, max_q,
        )
        df_missing = QuizReportService._build_missing_df(
            users_data, all_users,
        )

        # 4. Excel
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_summary.to_excel(writer, sheet_name="Сводка", index=False)
            df_details.to_excel(writer, sheet_name="Детально", index=False)
            df_missing.to_excel(writer, sheet_name="Не прошли", index=False)
            QuizReportService._format_sheets(writer, {
                "Сводка": df_summary,
                "Детально": df_details,
                "Не прошли": df_missing,
            })
        buffer.seek(0)
        return buffer

    @staticmethod
    async def send_report_to_admin(quiz_id: int) -> None:
        """Сгенерировать и отправить отчёт админу."""
        try:
            buffer = await QuizReportService.build_quiz_report(quiz_id=quiz_id)
        except Exception as e:
            logger.exception("Ошибка генерации отчёта quiz=%s: %s", quiz_id, e)
            await bot.send_message(
                chat_id=settings.MAIN_ADMIN,
                text=f"❌ Ошибка генерации отчёта по квизу {quiz_id}: {e}",
            )
            return

        try:
            await bot.send_document(
                chat_id=settings.MAIN_ADMIN,
                document=BufferedInputFile(
                    buffer.getvalue(),
                    filename=f"quiz_{quiz_id}_report_{datetime.now():%Y%m%d_%H%M}.xlsx",
                ),
                caption=f"📊 Отчёт по квизу ID={quiz_id}",
            )
            logger.info("Отчёт отправлен админу: quiz=%s", quiz_id)
        except Exception as e:
            logger.exception("Ошибка отправки отчёта: %s", e)

    # ==================== Данные ====================

    @staticmethod
    async def _get_answers_data(quiz_id: int) -> list[dict]:
        """Все ответы по квизу (JOIN с вопросами и ответами)."""
        from sqlalchemy import select
        from models import QuizResponse, QuizQuestion, QuizAnswer

        stmt = (
            select(
                QuizResponse.user_uuid.label("uuid"),
                QuizResponse.step,
                QuizResponse.is_correct,
                QuizQuestion.number.label("question_number"),
                QuizQuestion.text.label("question_text"),
                QuizAnswer.text.label("answer_text"),
                QuizAnswer.is_correct.label("answer_is_correct"),
                QuizResponse.date_create,
            )
            .join(QuizQuestion, QuizQuestion.id == QuizResponse.question_id)
            .join(QuizAnswer, QuizAnswer.id == QuizResponse.answer_id)
            .where(QuizResponse.quiz_id == quiz_id)
            .order_by(QuizResponse.user_uuid, QuizResponse.step)
        )
        async with db_helper.session_factory() as session:
            result = await session.execute(stmt)
            return [dict(row._mapping) for row in result.all()]

    @staticmethod
    async def _get_users_data(quiz_id: int) -> list[dict]:
        """Все QuizUser по квизу."""
        from sqlalchemy import select
        from models import QuizUser

        stmt = select(QuizUser).where(QuizUser.quiz_id == quiz_id)
        async with db_helper.session_factory() as session:
            result = await session.execute(stmt)
            return [
                {
                    "user_uuid": u.user_uuid,
                    "end_quiz": u.end_quiz,
                    "step": u.step,
                    "correct_count": u.correct_count,
                    "total_count": u.total_count,
                    "completed_at": u.completed_at,
                    "last_activity_at": u.last_activity_at,
                }
                for u in result.scalars().all()
            ]

    # ==================== Вкладка «Сводка» ====================

    @staticmethod
    def _build_summary_df(quiz, answers_data, users_data) -> pd.DataFrame:
        """Вкладка «Сводка» — распределение ответов."""
        passed = sum(1 for u in users_data if u["end_quiz"])
        abandoned = sum(1 for u in users_data if not u["end_quiz"])

        header_text = (
            f"Квиз: {quiz.title}\n"
            f"Период: {quiz.start_date:%d.%m.%Y} — {quiz.end_date:%d.%m.%Y}\n"
            f"Прошли: {passed}, бросили: {abandoned}"
        )

        if not answers_data:
            return pd.DataFrame([{
                "Вопрос №": "—",
                "Вопрос": header_text,
                "Ответ": "—",
                "Правильный": "—",
                "Выбрали": "—",
                "%": "—",
            }])

        df = pd.DataFrame(answers_data)
        grouped = (
            df.groupby(
                ["question_number", "question_text", "answer_text", "answer_is_correct"],
                as_index=False,
            )
            .size()
            .rename(columns={"size": "Выбрали"})
        )
        total_per_q = grouped.groupby("question_number")["Выбрали"].transform("sum")
        grouped["%"] = (grouped["Выбрали"] * 100 / total_per_q).round(1)

        grouped = grouped.rename(columns={
            "question_number": "Вопрос №",
            "question_text": "Вопрос",
            "answer_text": "Ответ",
            "answer_is_correct": "Правильный",
        })
        grouped["Правильный"] = grouped["Правильный"].apply(
            lambda x: "✅" if x else ""
        )

        header = pd.DataFrame([{
            "Вопрос №": "—",
            "Вопрос": header_text,
            "Ответ": "—",
            "Правильный": "—",
            "Выбрали": "—",
            "%": "—",
        }])
        return pd.concat([header, grouped], ignore_index=True)

    # ==================== Вкладка «Детально» ====================

    @staticmethod
    def _build_details_df(quiz, answers_data, users_data, all_users, max_q: int) -> pd.DataFrame:
        """Вкладка «Детально» — по пользователям."""
        # Pivot: user_uuid → {question_number: answer_text}
        pivot = {}
        for a in answers_data:
            pivot.setdefault(a["uuid"], {})[a["question_number"]] = a["answer_text"]

        users_map = {u["user_uuid"]: u for u in users_data}

        rows = []
        for user in all_users:
            uid = user["uuid"]
            quiz_user = users_map.get(uid)
            fio = " ".join(filter(None, [
                user.get("surname"), user.get("given_name"), user.get("middle_name"),
            ]))

            if quiz_user:
                status = "✅ Прошёл" if quiz_user["end_quiz"] else "⏳ Бросил"
                score = f"{quiz_user['correct_count']}/{quiz_user['total_count']}"
                date_str = (
                    quiz_user["completed_at"].strftime("%Y-%m-%d %H:%M")
                    if quiz_user["completed_at"] else ""
                )
            else:
                status = "❌ Не начинал"
                score = "—"
                date_str = ""

            row = {
                "uuid": uid,
                "ФИО": fio,
                "Группа": user.get("group", ""),
                "Статус": status,
                "Балл": score,
                "Дата": date_str,
            }
            for q_num in range(1, max_q + 1):
                row[f"Q{q_num}"] = pivot.get(uid, {}).get(q_num, "")
            rows.append(row)

        df = pd.DataFrame(rows)
        # Сортировка: прошедшие → бросившие → не начинавшие
        df["_sort"] = df["Статус"].map({
            "✅ Прошёл": 0,
            "⏳ Бросил": 1,
            "❌ Не начинал": 2,
        }).fillna(3)
        df = df.sort_values(["_sort", "uuid"]).drop(columns=["_sort"]).reset_index(drop=True)
        return df

    # ==================== Вкладка «Не прошли» ====================

    @staticmethod
    def _build_missing_df(users_data, all_users) -> pd.DataFrame:
        """Вкладка «Не прошли»."""
        users_map = {u["user_uuid"]: u for u in users_data}
        rows = []
        for user in all_users:
            uid = user["uuid"]
            quiz_user = users_map.get(uid)
            if quiz_user and quiz_user["end_quiz"]:
                continue   # прошёл — не включаем
            fio = " ".join(filter(None, [
                user.get("surname"), user.get("given_name"), user.get("middle_name"),
            ]))
            status = "⏳ Бросил" if quiz_user else "❌ Не начинал"
            rows.append({
                "uuid": uid,
                "ФИО": fio,
                "Группа": user.get("group", ""),
                "Телефон": user.get("phone", ""),
                "Email": user.get("email", ""),
                "Статус": status,
            })
        return pd.DataFrame(rows)

    # ==================== Форматирование ====================

    @staticmethod
    def _format_sheets(writer, sheets: dict):
        """Ширина колонок + жирные заголовки + заморозка."""
        for sheet_name, df in sheets.items():
            ws = writer.sheets[sheet_name]
            ws.freeze_panes = "A2"
            for idx, col in enumerate(df.columns, start=1):
                max_len = len(str(col))
                if not df.empty:
                    col_max = df[col].astype(str).str.len().max()
                    if pd.notna(col_max):
                        max_len = max(max_len, int(col_max))
                ws.column_dimensions[chr(64 + idx)].width = min(max_len + 2, 50)
            for cell in ws[1]:
                cell.font = cell.font.copy(bold=True)