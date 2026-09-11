import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import Scene, on
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.utils.chat_action import ChatActionSender

from services.sending_service import broadcast_text_all_users
from database.users_crud import load_recipients

logger = logging.getLogger(__name__)
router = Router(name="broadcast")


class BroadcastScene(Scene, state="broadcast"):

    # ---------- Вход в сцену ----------
    @on.message.enter()
    async def on_enter(self, message: Message, state: FSMContext) -> None:
        await state.update_data(phase="input_text", text=None, recipients=None)
        await message.answer(
            "✉️ Пришлите текст сообщения для рассылки.\n\n"
            "Отмена: /cancel"
        )

    # ---------- Отмена на любом шаге ----------
    @on.message(F.text == "/cancel")
    async def cancel_input(self, message: Message, state: FSMContext) -> None:
        await message.answer("❌ Рассылка отменена.")
        await self.wizard.exit()

    # ---------- Шаг 1: получаем текст ----------
    @on.message(F.text)
    async def got_text(self, message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        if data.get("phase") != "input_text":
            return  # игнорируем текст в других фазах

        await state.update_data(text=message.html_text)

        recipients = await load_recipients()
        await state.update_data(recipients=recipients, phase="confirm")

        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="📤 Отправить", callback_data="bc:send"),
            InlineKeyboardButton(text="✏️ Изменить", callback_data="bc:edit"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="bc:cancel"),
        ]])
        await message.answer(
            f"📋 <b>Предпросмотр:</b>\n\n{message.html_text}\n\n"
            f"👥 Получателей: <b>{len(recipients)}</b>",
            reply_markup=kb,
        )

    # ---------- Кнопки ----------
    @on.callback_query(F.data == "bc:cancel")
    async def cancel_confirm(self, callback: CallbackQuery, state: FSMContext) -> None:
        data = await state.get_data()
        if data.get("phase") != "confirm":
            await callback.answer()
            return
        await callback.message.edit_text("❌ Рассылка отменена.")
        await callback.answer()
        await self.wizard.exit()

    @on.callback_query(F.data == "bc:edit")
    async def edit_text(self, callback: CallbackQuery, state: FSMContext) -> None:
        data = await state.get_data()
        if data.get("phase") != "confirm":
            await callback.answer()
            return
        await state.update_data(phase="input_text", text=None)
        await callback.message.edit_text(
            "✏️ Пришлите новый текст.\n\nОтмена: /cancel"
        )
        await callback.answer()

    @on.callback_query(F.data == "bc:send")
    async def send(self, callback: CallbackQuery, state: FSMContext) -> None:
        data = await state.get_data()
        if data.get("phase") != "confirm":
            await callback.answer()
            return

        text: str = data["text"]
        recipients: list[str] = data["recipients"]

        await callback.message.edit_text("🚀 Рассылка запущена...")
        await callback.answer()
        async with ChatActionSender.typing(bot=callback.bot, chat_id=callback.message.chat.id):
            ok, failed = await broadcast_text_all_users(callback.bot, recipients, text)

        await callback.message.edit_text(
            f"✅ Готово.\n\n"
            f"Успешно: <b>{ok}</b>\n"
            f"Ошибок: <b>{failed}</b>"
        )
        await self.wizard.exit()