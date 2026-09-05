import logging
#
from aiogram import Router, F, flags, types
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.chat_action import ChatActionSender

from config import bot
from database.admin_crud import get_user_all, set_role
from database.users_crud import get_user_by_uuid
# from database.admin_crud import get_user_all, get_users_pools_join_user
# from database.dao.pool_repository import DAOPools
from filters.is_admin import IsAdmin
from keyboards.reply_keyboar import r_kb_cancel
from models import User
from services.admin_services import send_users_list, send_users_list_4096
from services.user_services import send_list
from states.admin_states import FSMSetUserToAdmin, FSMUserAnswers

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


#
#
# @router.message(Command(commands="list_users_pools"), IsAdmin())
# @flags.chat_action(action=ChatAction.TYPING)
# async def get_users_pools(message: Message):
#     data = await get_users_pools_join_user(user_uuid=None)
#     count: int = 1
#     items: list[str] = []
#     list_items: list[str] = []
#
#     for item in data:
#         if len(f"{count}, {item["user_uuid"]}, {item["first_name"]}, {item["pool_id"]}, {item["end_pool"]},"
#                f" {item["step"]}, {item["pool_category"].name}\n") + len("".join(items)) < 4096:
#             items.append(f"{count}, {item["user_uuid"]}, {item["first_name"]},"
#                          f" {item["pool_id"]}, {item["end_pool"]}, {item["step"]}, {item["pool_category"].name}\n")
#         else:
#             list_items.append("".join(items))
#             items.clear()
#             items.append(f"{count}, {item["user_uuid"]}, {item["first_name"]},"
#                          f"{item["pool_id"]}, {item["end_pool"]}, {item["step"]}, {item["pool_category"].name}\n")
#             count += 1
#     list_items.append("".join(items))
#     await send_list(message=message, data=list_items)
#
#
# @router.message(Command(commands="list_users_answers"), IsAdmin())
# @flags.chat_action(action=ChatAction.TYPING)
# async def get_users_answers(message: Message, state: FSMContext):
#     await state.set_state(FSMUserAnswers.get_id)
#     await message.answer(text=f"Введите ID пользователя ответы которого Вас интересуют."
#                               f"Или наберите /exit для выхода.")
#
#
# @router.message(F.text, FSMUserAnswers.get_id)
# async def get_users_answers(message: Message, state: FSMContext):
#     await state.clear()
#     data = await DAOPools.get_answer_by_user_id(user_uuid=message.text)
#     items: list[str] = []
#     list_items: list[str] = []
#     for item in data:
#         if len(f"{item["question_number"]}, {item["pool_question"]}\n\n"
#                f"ОТВЕТ: {item["pool_answer"]}\n\n") + len("".join(items)) < 4096:
#             items.append(f"<b>{item["question_number"]}, {item["pool_question"]}</b>\n\n"
#                          f"ОТВЕТ: <i>{item["pool_answer"]}</i>\n\n")
#         else:
#             list_items.append("".join(items))
#             items.clear()
#             items.append(f"<b>{item["question_number"]}, {item["pool_question"]}</b>\n\n"
#                          f"ОТВЕТ: <i>{item["pool_answer"]}</i>\n\n")
#             # count += 1
#     list_items.append("".join(items))
#     await send_list(message=message, data=list_items)
#
#
# @router.message(Command(commands="exit"), FSMUserAnswers)
# async def get_users_answers(message: Message, state: FSMContext):
#     await state.clear()
#     await message.answer(text="Успешно вышли.")
#
#
# # for item in data:
# #     if len(f"{count}, {item["user_uuid"]}, {item["first_name"]}, {item["pool_id"]}, {item["end_pool"]},"
# #            f" {item["step"]}, {item["pool_category"].name}\n") + len("".join(items)) < 4096:
# #         items.append(f"{count}, {item["user_uuid"]}, {item["first_name"]},"
# #                      f" {item["pool_id"]}, {item["end_pool"]}, {item["step"]}, {item["pool_category"].name}\n")
# #     else:
# #         list_items.append("".join(items))
# #         items.clear()
# #         items.append(f"{count}, {item["user_uuid"]}, {item["first_name"]},"
# #                      f"{item["pool_id"]}, {item["end_pool"]}, {item["step"]}, {item["pool_category"].name}\n")
# #         count += 1
# # list_items.append("".join(items))
# # await send_list(message=message, data=list_items)
#

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
