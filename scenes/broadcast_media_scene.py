import logging
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import Scene, on
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
)

from config import bot, settings
from services.recipients_services import RecipientsService
from services.scheduled_broadcast_service import ScheduledBroadcastService
from services.sending_service import broadcast_text_all_users, broadcast_photo_all_users, send_message_text_to_user
from services.services import _is_date

logger = logging.getLogger(__name__)


class BroadcastMediaScene(Scene, state="broadcast_media"):
    """Сцена создания рассылки: текст → фото → превью → сейчас / запланировать."""

    # ==================== Вход ====================

    @on.callback_query.enter()
    async def on_enter(self, callback: CallbackQuery, state: FSMContext):
        """Вход в сцену через inline-кнопку."""
        await callback.answer()
        await state.update_data(
            bc_text=None,
            bc_photo=None,
            bc_step="text",
        )

        await callback.message.answer(
            "📢 <b>Создание рассылки</b>\n\n"
            "Шаг 1/2: отправьте <b>текст</b> сообщения.\n"
            "Можно использовать HTML-разметку.\n\n"
            "Или /skip — если хотите отправить только фото.\n\n"
            "❌ /cancel — отмена.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="bc:cancel")],
            ]),
        )

    # ==================== Шаг 1: Текст (не дата) ====================

    @on.message(F.text, lambda m: m.text and not _is_date(m.text) and not m.text.startswith("/"))
    async def on_text(self, message: Message, state: FSMContext):
        """Получили текст рассылки (не дату)."""
        data = await state.get_data()
        if data.get("bc_step") != "text":
            return

        await state.update_data(bc_text=message.html_text, bc_step="photo")
        await self._ask_photo(message)

    @on.message(F.text == "/skip")
    async def on_skip_text(self, message: Message, state: FSMContext):
        """Пропустили текст — просим фото."""
        data = await state.get_data()
        if data.get("bc_step") != "text":
            return
        await state.update_data(bc_text=None, bc_step="photo")
        await self._ask_photo(message)

    async def _ask_photo(self, message: Message):
        await message.answer(
            "🖼 <b>Шаг 2/2: отправьте фото</b>\n\n"
            "Или /skip — если хотите отправить только текст.\n\n"
            "❌ /cancel — отмена.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="bc:cancel")],
            ]),
        )

    # ==================== Шаг 2: Фото ====================

    @on.message(F.photo)
    async def on_photo(self, message: Message, state: FSMContext):
        """Получили фото — показываем превью."""
        data = await state.get_data()
        if data.get("bc_step") != "photo":
            return
        file_id = message.photo[-1].file_id
        await state.update_data(bc_photo=file_id, bc_step="preview")
        await self._show_preview(message, state)

    @on.message(F.text == "/skip")
    async def on_skip_photo(self, message: Message, state: FSMContext):
        """Пропустили фото — показываем превью."""
        data = await state.get_data()
        if data.get("bc_step") != "photo":
            return
        await state.update_data(bc_photo=None, bc_step="preview")
        await self._show_preview(message, state)

    # ==================== Превью ====================

    async def _show_preview(self, message: Message, state: FSMContext):
        """Показывает превью и кнопки подтверждения."""
        data = await state.get_data()
        text = data.get("bc_text")
        photo = data.get("bc_photo")

        if not text and not photo:
            await message.answer("⚠️ Нет ни текста, ни фото. Начните заново /admin")
            await state.clear()
            await self.wizard.exit()
            return

        # Получатели — для отображения количества
        all_recipients = await RecipientsService.get_recipients()
        test_recipients = list(settings.TEST_USERS)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"✅ Отправить всем ({len(all_recipients)})",
                callback_data="bc:send_all",
            )],
            [InlineKeyboardButton(
                text=f"🧪 Только тестовым ({len(test_recipients)})",
                callback_data="bc:send_test",
            )],
            [InlineKeyboardButton(text="🕐 Запланировать", callback_data="bc:schedule")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="bc:cancel")],
        ])

        preview_text = (
            f"👀 <b>Предпросмотр</b>\n\n"
            f"{text or '<i>(без текста)</i>'}\n\n"
            f"👥 Всем: {len(all_recipients)} | 🧪 Тестовым: {len(test_recipients)}"
        )

        if photo:
            await message.answer_photo(
                photo=photo,
                caption=preview_text[:1024],
                parse_mode="HTML",
                reply_markup=keyboard,
            )
            if text and len(text) > 1024:
                await message.answer(
                    "⚠️ Текст длиннее 1024 символов — при отправке будет 2 сообщения (фото + текст)."
                )
        else:
            await message.answer(preview_text, parse_mode="HTML", reply_markup=keyboard)

    # ==================== Отправка сейчас ====================

    @on.callback_query(F.data == "bc:send_all")
    async def on_send_all(self, callback: CallbackQuery, state: FSMContext):
        recipients = await RecipientsService.get_recipients()
        await self._do_send(callback, state, recipients)

    @on.callback_query(F.data == "bc:send_test")
    async def on_send_test(self, callback: CallbackQuery, state: FSMContext):
        recipients = list(settings.TEST_USERS)
        await self._do_send(callback, state, recipients)

    async def _do_send(self, callback: CallbackQuery, state: FSMContext, recipients: list[str]):
        await callback.answer(f"🚀 Рассылка на {len(recipients)}...")

        data = await state.get_data()
        text = data.get("bc_text") or ""
        photo = data.get("bc_photo")

        if not recipients:
            await callback.message.answer("❌ Нет получателей")
            await state.clear()
            await self.wizard.exit()
            return

        await callback.message.answer(f"⏳ Рассылка на {len(recipients)}...")

        logger.warning("🚨 _do_send: получателей=%d, photo=%s", len(recipients), bool(photo))

        try:
            if photo:
                ok, failed, errors = await broadcast_photo_all_users(
                    bot=bot,
                    recipients=recipients,
                    photo=photo,
                    text=text,
                    save_last_message=True,
                )
            else:
                ok, failed, errors = await broadcast_text_all_users(
                    bot=bot,
                    recipients=recipients,
                    text=text,
                    save_last_message=True,
                )
            logger.warning("🚨 _do_send: ok=%d, failed=%d", ok, failed)
        except Exception as e:
            logger.exception("🚨 _do_send: ошибка: %s", e)
            await callback.message.answer(f"❌ Ошибка: {e}")
            await state.clear()
            await self.wizard.exit()
            return

        # result_text = self._format_result(len(recipients), ok, failed, errors)
        # await send_message_text_to_user(
        #     uuid=str(settings.MAIN_ADMIN),  # ← вот сюда
        #     text=result_text,
        # )
        await callback.message.answer(result_text, parse_mode="HTML")
        await state.clear()
        await self.wizard.exit()

    # ==================== Запланировать ====================

    @on.callback_query(F.data == "bc:schedule")
    async def on_schedule(self, callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        await state.update_data(bc_step="schedule_input")

        await callback.message.answer(
            "🕐 <b>Планирование рассылки</b>\n\n"
            "Введите дату и время в формате:\n"
            "<code>2026-11-11 09:00</code>\n\n"
            "❌ /cancel — отмена.",
            parse_mode="HTML",
        )

    @on.message(F.text, lambda m: m.text and _is_date(m.text))
    async def on_schedule_input(self, message: Message, state: FSMContext):
        """Получили дату в правильном формате."""
        logger.warning("🚨 on_schedule_input CALLED: text=%s", message.text)

        data = await state.get_data()
        if data.get("bc_step") != "schedule_input":
            logger.warning("🚨 on_schedule_input: bc_step=%s — пропускаю", data.get("bc_step"))
            return

        try:
            scheduled_at = datetime.strptime(message.text.strip(), "%Y-%m-%d %H:%M")
            scheduled_at = scheduled_at.replace(tzinfo=ZoneInfo("Europe/Minsk"))
        except ValueError as e:
            logger.warning("🚨 on_schedule_input: strptime error: %s", e)
            await message.answer(
                "❌ Неверный формат. Используйте: <code>2026-11-11 09:00</code>",
                parse_mode="HTML",
            )
            return

        if scheduled_at <= datetime.now(ZoneInfo("Europe/Minsk")):
            await message.answer("❌ Время уже прошло. Введите будущее время.")
            return

        bc = await ScheduledBroadcastService.schedule(
            text=data.get("bc_text"),
            photo_file_id=data.get("bc_photo"),
            scheduled_at=scheduled_at,
            created_by=str(message.from_user.id),
        )
        logger.warning("🚨 on_schedule_input: запланировано id=%s", bc.id)

        await message.answer(
            f"✅ <b>Рассылка запланирована</b>\n"
            f"ID: <code>{bc.id}</code>\n"
            f"Время: {scheduled_at:%d.%m.%Y %H:%M}",
            parse_mode="HTML",
        )
        await state.clear()
        await self.wizard.exit()

    # ==================== Отмена ====================

    @on.callback_query(F.data == "bc:cancel")
    async def on_cancel(self, callback: CallbackQuery, state: FSMContext):
        await callback.answer("Отменено")
        await callback.message.answer("❌ Рассылка отменена.")
        await state.clear()
        await self.wizard.exit()

    @on.message(F.text == "/cancel")
    async def on_cancel_text(self, message: Message, state: FSMContext):
        await message.answer("❌ Рассылка отменена.")
        await state.clear()
        await self.wizard.exit()

    # ==================== Хелпер ====================

    @staticmethod
    def _format_result(total: int, ok: int, failed: int, errors: list[dict]) -> str:
        text = (
            f"📤 <b>Рассылка завершена</b>\n\n"
            f"Всего: {total}\n"
            f"✅ Успешно: {ok}\n"
            f"❌ Ошибок: {failed}"
        )
        if errors:
            lines = "\n".join(
                f"• {e.get('chat_id', e.get('raw_id', '?'))}: {e.get('reason', '?')}"
                for e in errors[:10]
            )
            text += f"\n\n⚠️ <b>Ошибки:</b>\n{lines}"
            if len(errors) > 10:
                text += f"\n... и ещё {len(errors) - 10}"
        return text