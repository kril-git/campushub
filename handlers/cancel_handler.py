import logging
from typing import Any

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(Command("cancel_global"), StateFilter(Any))
@router.message(F.text.casefold() == "выход", StateFilter(Any))
async def global_message_cancel(message: Message, state: FSMContext):
    if await state.get_state() is None:
        return
    await state.clear()  # Сбрасываем Redis
    await message.answer(
        "❌ Действие прервано. Вы вернулись в главное меню.",
        reply_markup=ReplyKeyboardRemove()
    )


@router.callback_query(
    F.data.startswith("cancel") |
    F.data.startswith("exit") |
    F.data.startswith("quit"),
    StateFilter(any)
)
async def global_callback_cancel(callback: CallbackQuery, state: FSMContext):
    if await state.get_state() is None:
        await callback.answer()
        return

    # 1. Сразу гасим часики на кнопке
    await callback.answer("Действие отменено")

    # 2. Жестко чистим FSM в Redis
    await state.clear()

    # 3. Удаляем сообщение со старыми кнопками, чтобы чат был чистым
    try:
        await callback.message.delete()
    except Exception:
        pass

    # 4. Отправляем уведомление в чат
    await callback.message.answer(
        "❌ Вы отменили действие и вышли в главное меню.",
        reply_markup=ReplyKeyboardRemove()
    )
