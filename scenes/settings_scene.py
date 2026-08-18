from typing import Any

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm import scene
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import Scene, on
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram import F

router = Router(name=__name__)


class SettingsScene(Scene, state="settings_scene"):
    keyboard = [
        [InlineKeyboardButton(text="Пpoфиль", callback_data="profile")],
        [InlineKeyboardButton(text="Дocтижeния", callback_data="achievements")],
        [InlineKeyboardButton(text="Пoдпиcки", callback_data="suЬscriptions")],
        [InlineKeyboardButton(text="Bыйти", callback_data="exit")],
    ]

    @on.message.enter()
    async def on_enter(self, message: Message, state: FSMContext):
        # return
        await message.answer(text="Зто ваши настройки. Выберите пункт ниже",
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=self.keyboard)
                             )

    @on.callback_query(F.data == "exit")
    async def on_enter_cb(self, callback: CallbackQuery):
        await callback.message.answer(text="CallbackQuery")
        await self.wizard.exit()


    @on.message(F.text == "zzz")
    async def echo_scene(self, message: Message):
        await message.answer(text="echo_scene")

    #
    # @on.callback_query.enter(F.data == "exit")
    # async def exit(self, callback: CallbackQuery, state: FSMContext):
    #     await callback.message.answer(
    #         text="EXIT"
    #     )
    #     await self.wizard.exit()
    #
    # @on.message.exit()
    # async def exit(self, message: Message):
    #     await message.answer("Вышли из сцены")
    #
    # @on.message(F.text)
    # async def answer(self, message: Message, state: FSMContext) -> None:
    #     print("in scem")
    #
    # @on.message()
    # # @Action(F.text)
    # async def unknown_message(self, message: Message) -> None:
    #     await message.answer("Please select an answer.")

    @on.callback_query.exit()
    async def exit(self, callback: CallbackQuery, state: FSMContext):
        await callback.message.answer(text="вышли из сцены")
        await state.clear()
        current_state = await state.get_state()
        await callback.message.answer(f"Текущее состояние: {current_state}")


# pip install -U aiogram
# python3 -m pip install -U aiogram
router.message.register(SettingsScene.as_handler(), Command("settings"))
