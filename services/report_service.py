# services/report_service.py
import logging
from io import BytesIO
from datetime import datetime

import pandas as pd
from openpyxl.styles import Alignment
from aiogram.types import BufferedInputFile

from config import bot, settings
from database.dao.report_dao import ReportDAO
from services.pool_service import PoolService

logger = logging.getLogger(__name__)


def _norm_phone(phone: str | None) -> str:
    """Нормализует телефон: +375..., 375... → +375..."""
    if not phone:
        return ""
    p = phone.strip()
    if not p:
        return ""
    return p if p.startswith("+") else f"+{p}"


class ReportService:

    # ===== Публичные методы =====

    @staticmethod
    async def build_pool_report(pool_id: int) -> BytesIO:
        """Генерирует Excel-отчёт по опросу pool_id в памяти."""
        pool = await PoolService.get_object_pool(id_pool=pool_id)
        if not pool:
            raise ValueError(f"Пул {pool_id} не найден")

        answers = await ReportDAO.get_answers_with_users(pool_id=pool_id)
        all_users = await ReportDAO.get_all_users_with_info()
        statuses = await ReportDAO.get_completion_status(pool_id=pool_id)
        max_q = await PoolService.get_count_questions(pool_id=pool_id)

        df_summary = ReportService._build_summary_df(pool, answers, all_users, statuses)
        df_details = ReportService._build_details_df(answers, all_users, statuses, max_q)
        df_missing = ReportService._build_missing_df(all_users, statuses)

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_summary.to_excel(writer, sheet_name="Сводка", index=False)
            df_details.to_excel(writer, sheet_name="Детально", index=False)
            df_missing.to_excel(writer, sheet_name="Не прошли", index=False)
            ReportService._format_sheets(writer, {
                "Сводка": df_summary,
                "Детально": df_details,
                "Не прошли": df_missing,
            })

        buffer.seek(0)
        return buffer

    @staticmethod
    async def send_pool_report_to_admin(pool_id: int) -> None:
        """Генерирует отчёт и отправляет админу."""
        try:
            buffer = await ReportService.build_pool_report(pool_id=pool_id)
        except Exception as e:
            logger.exception("Ошибка генерации отчёта pool=%s: %s", pool_id, e)
            await bot.send_message(
                chat_id=settings.MAIN_ADMIN,
                text=f"❌ Ошибка генерации отчёта по пулу {pool_id}: {e}",
            )
            return

        try:
            await bot.send_document(
                chat_id=settings.MAIN_ADMIN,
                document=BufferedInputFile(
                    buffer.getvalue(),
                    filename=f"pool_{pool_id}_report_{datetime.now():%Y%m%d_%H%M}.xlsx",
                ),
                caption=f"📊 Отчёт по опросу pool={pool_id}",
            )
            logger.info("Отчёт отправлен админу: pool=%s", pool_id)
        except Exception as e:
            logger.exception("Ошибка отправки отчёта: %s", e)

    # ===== Приватные: DataFrame'ы =====

    @staticmethod
    def _build_summary_df(pool, answers, all_users, statuses) -> pd.DataFrame:
        """Вкладка «Сводка» — агрегаты по вопросам."""
        total = len(all_users)
        passed = sum(1 for s in statuses if s.get("end_pool") is True)

        header_text = (
            f"Опрос: {pool.pool_description}\n"
            f"Период: {pool.start_date} — {pool.end_date}\n"
            f"Всего: {total}, прошли: {passed}, не прошли: {total - passed}"
        )

        if not answers:
            return pd.DataFrame([{
                "Вопрос №": "—",
                "Вопрос": header_text,
                "Ответ": "—",
                "Количество": "—",
                "%": "—",
            }])

        df = pd.DataFrame(answers)
        grouped = (
            df.groupby(["question_number", "pool_question", "pool_answer"], as_index=False)
            .size()
            .rename(columns={"size": "Количество"})
        )
        total_per_q = grouped.groupby("question_number")["Количество"].transform("sum")
        grouped["%"] = (grouped["Количество"] * 100 / total_per_q).round(1)

        grouped = grouped.rename(columns={
            "question_number": "Вопрос №",
            "pool_question": "Вопрос",
            "pool_answer": "Ответ",
        })

        header = pd.DataFrame([{
            "Вопрос №": "—",
            "Вопрос": header_text,
            "Ответ": "—",
            "Количество": "—",
            "%": "—",
        }])
        return pd.concat([header, grouped], ignore_index=True)

    @staticmethod
    def _build_details_df(answers, all_users, statuses, max_q: int) -> pd.DataFrame:
        """Вкладка «Детально» — pivot по пользователям. Сортировка: сначала прошедшие."""
        status_map = {s["uuid"]: s for s in statuses}

        pivot = {}
        for a in answers:
            pivot.setdefault(a["uuid"], {})[a["question_number"]] = a["pool_answer"]

        rows = []
        for user in all_users:
            uid = user["uuid"]
            status = status_map.get(uid, {})
            is_passed = status.get("end_pool") is True
            fio = " ".join(filter(None, [
                user.get("surname"), user.get("given_name"), user.get("middle_name"),
            ]))
            date_update = status.get("date_update")
            row = {
                "uuid": uid,
                "ФИО": fio,
                "Группа": user.get("group", ""),
                "Статус": "✅ Прошёл" if is_passed else "❌ Не прошёл",
                "Дата": date_update.strftime("%Y-%m-%d %H:%M") if date_update else "",
                "_passed": 0 if is_passed else 1,   # ← для сортировки
            }
            for i in range(1, max_q + 1):
                row[f"Вопрос {i}"] = pivot.get(uid, {}).get(i, "")
            rows.append(row)

        df = pd.DataFrame(rows)
        # ✅ Сначала прошедшие (0), потом не прошедшие (1), внутри — по uuid
        df = df.sort_values(by=["_passed", "uuid"]).drop(columns=["_passed"]).reset_index(drop=True)
        return df

    @staticmethod
    def _build_missing_df(all_users, statuses) -> pd.DataFrame:
        """Вкладка «Не прошли». Телефоны нормализованы."""
        status_map = {s["uuid"]: s for s in statuses}
        rows = []
        for user in all_users:
            uid = user["uuid"]
            status = status_map.get(uid, {})
            if status.get("end_pool") is True:
                continue
            fio = " ".join(filter(None, [
                user.get("surname"), user.get("given_name"), user.get("middle_name"),
            ]))
            rows.append({
                "uuid": uid,
                "ФИО": fio,
                "Группа": user.get("group", ""),
                "Телефон": _norm_phone(user.get("phone")),   # ← нормализация
                "Email": user.get("email", ""),
                "Статус": "❌ Не прошёл",
            })
        return pd.DataFrame(rows)

    @staticmethod
    def _format_sheets(writer, sheets: dict):
        """
        Ширина колонок + жирные заголовки + заморозка первой строки + wrap.
        - Вопрос / ФИО — шире (50).
        - Остальные — по содержимому.
        """
        for sheet_name, df in sheets.items():
            ws = writer.sheets[sheet_name]

            # ✅ Заморозка первой строки (заголовки всегда видны)
            ws.freeze_panes = "A2"

            for idx, col in enumerate(df.columns, start=1):
                col_letter = chr(64 + idx)   # A, B, C, ...
                max_len = len(str(col))
                if not df.empty:
                    col_max = df[col].astype(str).str.len().max()
                    if pd.notna(col_max):
                        max_len = max(max_len, int(col_max))

                # ✅ Для длинных колонок — фиксированная ширина + wrap
                if col in ("Вопрос", "ФИО", "Email"):
                    ws.column_dimensions[col_letter].width = 50
                    for row in ws.iter_rows(min_row=1, min_col=idx, max_col=idx):
                        for cell in row:
                            cell.alignment = Alignment(wrap_text=True, vertical="top")
                else:
                    ws.column_dimensions[col_letter].width = min(max_len + 2, 50)

            # ✅ Жирный заголовок
            for cell in ws[1]:
                cell.font = cell.font.copy(bold=True)