# import logging
# from aiogram import Router, F, flags
# from aiogram.enums import ChatAction
# from aiogram.filters import CommandStart, Command
# from aiogram.fsm.context import FSMContext
# from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
# from aiogram.utils.chat_action import ChatActionSender
#
# from config import bot
# from database.admin_crud import set_role, get_user_all
# from database.users_crud import if_exist_user, create_new_user, update_last_visit
# from filters.is_admin import IsAdmin
# from filters.states_is_not_none import IsNotNoneStates
# from keyboards.inline_keyboard import i_kb_yes_or_no
# from keyboards.reply_keyboar import r_kb_cancel, r_kb_accounting
# from models import User
# from services.admin_services import send_users_list, send_users_list_4096
# from states.admin_states import FSMSetUserToAdmin
# from states.products_states import FSMProducts
# from config.constants import product_sep, product_template
#
# router = Router(name=__name__)
# logger = logging.getLogger(__name__)
#
#
# # @router.message(Command(commands="products"))
# # async def create_menu_accounting(message: Message, state: FSMContext):
# #     await state.set_state(FSMProducts.products)
# #     await message.answer(text="Перешли в раздел управления ассортиментом.", reply_markup=r_kb_accounting)
#
#
# @router.message(F.text.lower().contains("добавить".lower()), FSMProducts.products)
# async def add_product(message: Message, state: FSMContext):
#     await state.set_state(FSMProducts.add)
#     # await state.set_data("uuid", message.from_user.id)
#     await state.update_data(uuid=message.from_user.id)
#     await message.answer(text=f"Введите наименование товара, далее поставьте разделитель -> {product_sep} после этого "
#                               f"введите"
#                               f"описание товара и завершите его символом {product_sep} затем укажите стоимость в "
#                               f"формате 0.99 что"
#                               f"означает 99 копеек")
#
#
# @router.message(F.text, FSMProducts.add)
# async def add_product(message: Message, state: FSMContext):
#     text_data = message.text.split(sep="#")
#     data = await state.get_data()
#     return_dict = {}
#     if len(text_data) == len(product_template):
#         for i in range(len(text_data)):
#             return_dict.update({product_template.get(str(i)): text_data[i]})
#
#     await state.update_data(return_dict)
#     data = await state.get_data()
#     temp_str: str = ""
#     for k, v in data.items():
#         temp_str += f"<b>{k}</b> - <i>{v}</i>\n"
#     temp_str += f"\n\n<b>Все правильно? Если все хорошо, нажмите ДА, иначе нажмите НЕТ и начните с начала.</b>"
#     await message.answer(text=temp_str, parse_mode="HTML", reply_markup=i_kb_yes_or_no)
#     # Морковь#Морковка сырая#0.99
#     await state.set_state(FSMProducts.add_ok_no_ok)
#
#
# @router.callback_query(FSMProducts.add_ok_no_ok, F.data == "product_add_yes")
# async def add_product(callback: CallbackQuery, state: FSMContext):
#     await callback.message.edit_reply_markup(reply_markup=None)
#
#     await callback.message.answer(text="))")
#
#
# @router.callback_query(FSMProducts.add_ok_no_ok, F.data == "product_add_no")
# async def add_product(callback: CallbackQuery, state: FSMContext):
#     await callback.message.edit_reply_markup(reply_markup=None)
#     await state.set_state(FSMProducts.products)
#     await callback.message.answer(text="Записываю в базу данных", editMessageReplyMarkup=None)
#
#
# @router.message(F.text.lower() == "выход".lower(), IsNotNoneStates())
# async def exit_products(message: Message, state: FSMContext):
#     await state.clear()
#     await message.answer(text="Вышли из меню ТОВАРОВ!", reply_markup=ReplyKeyboardRemove())
