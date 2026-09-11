import logging
#
from aiogram import Router, F, flags, types
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.chat_action import ChatActionSender

from config import bot
from database.admin_crud import get_user_all, set_role, export_users_to_excel
from database.users_crud import get_user_by_uuid
from filters.is_admin import IsAdmin
from keyboards.reply_keyboar import r_kb_cancel
from models import User
from services.admin_services import send_users_list, send_users_list_4096
from states.admin_states import FSMSetUserToAdmin

router = Router(name=__name__)
logger = logging.getLogger(__name__)


# рабочий
@router.message(Command(commands="list_users"), IsAdmin())
@flags.chat_action(action=ChatAction.TYPING)
async def get_users(message: Message):
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        users: list[User] = await get_user_all()
        count = await send_users_list_4096(message=message, users=users)
        await message.answer(text=f"Итого зарегистрированною {count} пользователей")


@router.message(Command("export_users_to_exel"), IsAdmin())
async def export_users_command(message: types.Message):
    await message.answer("⏳ Формирую отчёт...")

    # Вызываем функцию (сессия передаётся через @connection)
    excel_file = await export_users_to_excel(return_bytes=True)  # type: ignore

    if excel_file:
        await message.answer_document(
            types.BufferedInputFile(
                excel_file.getvalue(),
                filename="users.xlsx"
            ),
            caption="📊 Отчёт по пользователям"
        )
    else:
        await message.answer("❌ Нет данных для экспорта")


# рабочий
@router.message(Command(commands="create_admin"), IsAdmin())
@flags.chat_action(action=ChatAction.TYPING)
async def set_user_to_admin(message: Message, state: FSMContext):
    users: list[User] = await get_user_all()
    await send_users_list(message=message, users=users)
    await state.set_state(FSMSetUserToAdmin.fill_uuid)
    await message.answer(text=f"Введите ID пользователя. \nИли нажмите ОТМЕНА. 👇",
                         reply_markup=r_kb_cancel)


# рабочий
@router.message(FSMSetUserToAdmin.fill_uuid, F.text.isnumeric())
@flags.chat_action(action=ChatAction.TYPING)
async def set_role_to_admin(message: Message, state: FSMContext):
    if await get_user_by_uuid(uuid=message.text) is not None:  # type: ignore
        await message.answer(text=f"Отлично, меняю роль для пользователя с UUID = {message.text}",
                             reply_markup=types.ReplyKeyboardRemove())
        user: User = await set_role(uuid=message.text)  # type: ignore
        await state.clear()
        await message.answer(text=f"{user.uuid}, {user.first_name}, {user.role}")
    else:
        await message.answer(
            text=f"Что то не так в UUID = {message.text}, такого пользователя нет.\n Попробуйте снова.")


# рабочий
@router.message(FSMSetUserToAdmin.fill_uuid, F.text.contains("Отмена"))
async def cancel(message: Message, state: FSMContext):
    await message.answer(text=f"ОК")
    await state.clear()
