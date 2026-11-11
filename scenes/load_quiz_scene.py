import io
import json
import logging

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import Scene, on
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
)

from config import settings
from services.quiz_service import QuizService, ValidationError

logger = logging.getLogger(__name__)


class LoadQuizScene(Scene, state="load_quiz"):
    """Сцена загрузки JSON-квиза в БД."""

    # ==================== Вход ====================

    @on.callback_query.enter()
    async def on_enter(self, callback: CallbackQuery, state: FSMContext):
        """Вход через inline-кнопку."""
        await callback.answer()
        await state.update_data(quiz_data=None, step="waiting_file")

        await callback.message.answer(
            "📄 <b>Загрузка квиза</b>\n\n"
            "Отправьте JSON-файл с квизом.\n"
            "Или /cancel для отмены.",
            parse_mode="HTML",
        )

    # ==================== Шаг: файл ====================

    @on.message(F.document)
    async def on_document(self, message: Message, state: FSMContext):
        """Получили документ — проверяем и валидируем."""
        if str(message.from_user.id) not in settings.ADMINS:
            await message.answer("❌ Нет доступа")
            return

        doc = message.document

        # 1. Проверка расширения
        if not doc.file_name.lower().endswith(".json"):
            await message.answer("❌ Нужен файл с расширением .json")
            return

        # 2. Скачиваем
        try:
            file = await message.bot.get_file(doc.file_id)
            buf = io.BytesIO()
            await message.bot.download_file(file.file_path, buf)
            buf.seek(0)
            content = buf.read().decode("utf-8")
        except Exception as e:
            logger.exception("Ошибка скачивания файла: %s", e)
            await message.answer(f"❌ Ошибка скачивания файла: {e}")
            return

        # 3. Парсим JSON
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            await message.answer(
                f"❌ <b>Ошибка JSON</b>\n\n"
                f"<code>{e}</code>\n\n"
                f"Строка {e.lineno}, позиция {e.colno}",
                parse_mode="HTML",
            )
            return

        # 4. Валидация
        errors = await QuizService.validate_full(data=data)
        if errors:
            error_text = "\n".join(f"• {e}" for e in errors)
            await message.answer(
                f"❌ <b>Ошибки в JSON</b>\n\n{error_text}\n\n"
                f"Исправьте и отправьте файл снова.",
                parse_mode="HTML",
            )
            return

        # 5. Сохраняем в state, показываем превью
        await state.update_data(quiz_data=data, step="preview")
        await self._show_preview(message, state)

    # ==================== Шаг: превью ====================

    async def _show_preview(self, message: Message, state: FSMContext):
        """Показывает превью квиза и кнопки."""
        data = await state.get_data()
        quiz_data = data.get("quiz_data")

        if not quiz_data:
            await message.answer("❌ Нет данных. Начните заново /load_quiz")
            await state.clear()
            await self.wizard.exit()
            return

        title = quiz_data.get("title", "—")
        description = quiz_data.get("description") or "—"
        start_date = quiz_data.get("start_date", "—")
        end_date = quiz_data.get("end_date", "—")
        questions_count = len(quiz_data.get("questions", []))

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Загрузить в БД", callback_data="lq:confirm")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="lq:cancel")],
        ])

        await message.answer(
            f"✅ <b>JSON валиден</b>\n\n"
            f"📝 <b>Название:</b> {title}\n"
            f"📄 <b>Описание:</b> {description}\n"
            f"📅 <b>Период:</b> {start_date} — {end_date}\n"
            f"❓ <b>Вопросов:</b> {questions_count}\n\n"
            f"Загрузить в БД?",
            parse_mode="HTML",
            reply_markup=keyboard,
        )

    # ==================== Шаг: загрузка ====================

    @on.callback_query(F.data == "lq:confirm")
    async def on_confirm(self, callback: CallbackQuery, state: FSMContext):
        """Загружаем квиз в БД."""
        await callback.answer("⏳ Загружаю...")

        data = await state.get_data()
        quiz_data = data.get("quiz_data")

        if not quiz_data:
            await callback.message.edit_text("❌ Нет данных. Начните заново /load_quiz")
            await state.clear()
            await self.wizard.exit()
            return

        try:
            quiz_id = await QuizService.load_from_json(
                data=quiz_data,
                created_by=str(callback.from_user.id),
            )
        except ValidationError as e:
            error_text = "\n".join(f"• {err}" for err in e.errors)
            await callback.message.edit_text(
                f"❌ <b>Ошибки валидации</b>\n\n{error_text}",
                parse_mode="HTML",
            )
            return
        except Exception as e:
            logger.exception("Ошибка загрузки квиза: %s", e)
            await callback.message.edit_text(f"❌ Ошибка загрузки: {e}")
            return

        await callback.message.edit_text(
            f"✅ <b>Квиз загружен</b>\n\n"
            f"ID: <code>{quiz_id}</code>\n"
            f"Название: {quiz_data.get('title', '—')}\n"
            f"Вопросов: {len(quiz_data.get('questions', []))}\n"
            f"Статус: <b>DRAFT</b>\n\n"
            f"Теперь его можно активировать и запустить.",
            parse_mode="HTML",
        )

        await state.clear()
        await self.wizard.exit()

    # ==================== Отмена ====================

    @on.callback_query(F.data == "lq:cancel")
    async def on_cancel(self, callback: CallbackQuery, state: FSMContext):
        await callback.answer("Отменено")
        await callback.message.edit_text("❌ Загрузка отменена.")
        await state.clear()
        await self.wizard.exit()

    @on.message(F.text == "/cancel")
    async def on_cancel_text(self, message: Message, state: FSMContext):
        await message.answer("❌ Загрузка отменена.")
        await state.clear()
        await self.wizard.exit()