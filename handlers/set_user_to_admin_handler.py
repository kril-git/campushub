import logging

from aiogram import Router, F, flags, types
from aiogram.enums import ChatAction
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database.admin_crud import set_role, get_user_all
from database.users_crud import if_exist_user, create_new_user, update_last_visit, get_user_by_uuid
from filters.is_admin import IsAdmin
from models import User
from services.admin_services import send_users_list
from states.admin_states import FSMSetUserToAdmin

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(FSMSetUserToAdmin.fill_uuid, F.text.isnumeric())
@flags.chat_action(action=ChatAction.TYPING)
async def set_role_to_admin(message: Message, state: FSMContext):
    if await get_user_by_uuid(uuid=message.text) is not None:
        await message.answer(text=f"Отлично, меняю роль для пользователя с UUID = {message.text}",
                             reply_markup=types.ReplyKeyboardRemove())
        user: User = await set_role(uuid=message.text)
        await state.clear()
        await message.answer(text=f"{user.uuid}, {user.first_name}, {user.role}")
    else:
        await message.answer(
            text=f"Что то не так в UUID = {message.text}, такого пользователя нет.\n Попробуйте снова.")


@router.message(FSMSetUserToAdmin.fill_uuid, F.text.contains("Отмена"))
async def cancel(message: Message, state: FSMContext):
    await message.answer(text=f"ОК")
    await state.clear()


@router.message(FSMSetUserToAdmin.fill_uuid, F.text)
async def error_message(message: Message, state: FSMContext):
    if message.text.lower() == "отмена":
        await message.answer(text=f"ОК")
        await state.clear()
    else:
        await message.answer(text=f"😟 UUID пользователя должен содержать только цифры.\nПопробуйте снова.")
