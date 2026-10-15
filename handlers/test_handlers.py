import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from core.config import settings
from filters.is_admin import IsAdmin
from services.EnumPools import PoolCategory
from services.pool_service import PoolService
from services.scheduled_jobs import mark_as_deleted_pool_job

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "_campushub_test_active_pool_", IsAdmin())
async def create_menu_accounting(callback: CallbackQuery):
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(f"Пришли в _campushub_test_active_pool_")
    await mark_as_deleted_pool_job()


@router.callback_query(F.data == "_get_active_pool_id_", IsAdmin())
async def get_active_pool_id(callback: CallbackQuery):
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(f"Пришли в _get_active_pool_id_")
    pool_id = await PoolService.get_active_pool_id(pool_category=PoolCategory.NONE)
    await callback.message.answer(f"Активный опрос ID = {pool_id}")

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
