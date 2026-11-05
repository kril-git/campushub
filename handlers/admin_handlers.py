import logging
#
from aiogram import Router, F, flags, types
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import bot
from core.config import settings
from database.admin_crud import get_user_all, set_role, export_users_to_excel, get_personal_record_short
from keyboards.inline_keyboard import create_i_kb_from_dict
from lexicon.lexicon import LEXICON_ADMIN_TEST
from services.personal_record_service import get_personal_record_short_lines, get_personal_record_short_lines_render
from database.dao.personal_record_dao import PersonalRecordDAO
from database.users_crud import get_user_by_uuid
from filters.is_admin import IsAdmin
from keyboards.reply_keyboar import r_kb_cancel
from models import User
from services.admin_services import send_users_list_4096, split_into_chunks, send_chunks, split_strings_into_chunks
from services.pool_service import PoolService
from services.render import render_users
from services.report_service import ReportService
from states.admin_states import FSMSetUserToAdmin

router = Router(name=__name__)
logger = logging.getLogger(__name__)


# рабочий
@router.message(Command(commands="list_users"), IsAdmin())
@flags.chat_action(action=ChatAction.TYPING)
async def get_users(message: Message):
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        users: list[User] = await get_user_all()  # type: ignore
        lines = [render_users(i, u) for i, u in enumerate(users, start=1)]
        chunks, total = split_strings_into_chunks(lines, limit=settings.MAX_MESSAGE_LENGTH)
        await send_chunks(message, chunks=chunks)

        await message.answer(text=f"Итого зарегистрированною {total} пользователей.\n"
                                  f"Количество chunks {len(chunks)}.")


@router.message(Command(commands="get_person_data_short"), IsAdmin())
async def get_person_data(message: Message):
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        lines: list[str] = await get_personal_record_short()  # type: ignore
        # lines: list[str] = await get_personal_record_short_lines_render()  # type: ignore
        chunks, total = split_strings_into_chunks(lines)
        await send_chunks(message, chunks=chunks)
        await message.answer(text=f"Итого зарегистрированною {total} пользователей.\n"
                                  f"Количество chunks {len(chunks)}.")


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
    # await send_users_list(message=message, users=users)
    render_users = lambda i, u: f"{i}, {u.uuid}, {u.first_name}, {u.role.name}, {u.registration}\n"
    chunks, total_lines = split_into_chunks(users, render_users, limit=settings.MAX_MESSAGE_LENGTH)

    await send_chunks(message, chunks=chunks)
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


@router.message(Command(commands="test"), IsAdmin())
async def test(message: Message):
    data = {
        "/test11": "/test12",
        "/test2": "/test2"
    }
    kbd = create_i_kb_from_dict(data=data, adjust=2)
    await message.answer(text="Админские дела", reply_markup=kbd)

    pass


@router.callback_query(F.data.startswith("_get_recent_pools_"), IsAdmin())
async def callback_text_1(callback: CallbackQuery):
    await callback.answer()
    await callback.message.delete()

    await callback.message.answer(text="нажали test1")
    # ✅ Последние 5 пулов
    pools = await PoolService.get_recent_pools(limit=5)
    if not pools:
        await callback.message.answer("Нет пулов")
        return

    builder = InlineKeyboardBuilder()
    for pool in pools:
        # Обрезаем описание, добавляем статус
        desc = (pool.pool_description or "")[:30]
        status = "🟢" if pool.pool_action.value == "ACTION" else "⚪"
        # Формат: "🟢 28: ПРОФИЛАКТИКА СУИЦИД..."
        builder.button(
            text=f"{status} {pool.id}: {desc}",
            callback_data=f"get_recent_pools:{pool.id}",
        )
    builder.adjust(1)
    await callback.message.answer(
        "Выбери пул для теста (5 последних):",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("get_recent_pools"))
async def on_test_report_click(callback: CallbackQuery):
    if str(callback.from_user.id) not in settings.ADMINS:
        await callback.answer("Нет доступа", show_alert=True)
        return

    _, pool_id_str = callback.data.split(":")
    try:
        pool_id = int(pool_id_str)
    except ValueError:
        await callback.answer("Неверный pool_id", show_alert=True)
        return

    await callback.answer(f"Генерирую отчёт pool={pool_id}")

    # Показываем сообщение о процессе
    progress_msg = await callback.message.answer(
        f"⏳ Генерирую отчёт по пулу {pool_id}..."
    )

    try:
        await ReportService.send_pool_report_to_admin(pool_id=pool_id)
        await progress_msg.edit_text(f"✅ Отчёт по пулу {pool_id} отправлен")
    except Exception as e:
        logger.exception("Ошибка test_report pool=%s: %s", pool_id, e)
        await progress_msg.edit_text(f"❌ Ошибка: {e}")


@router.message(Command(commands="_campushub_test_"), IsAdmin())
async def test(message: Message):
    kbd = create_i_kb_from_dict(data=LEXICON_ADMIN_TEST, adjust=1)
    await message.answer(text="Доступные тесты.", reply_markup=kbd)


@router.message(Command("test_report"))
async def cmd_test_report(message: Message):
    if str(message.from_user.id) not in settings.ADMINS:
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("Использование: /test_report <pool_id>")
        return

    try:
        pool_id = int(args[1])
    except ValueError:
        await message.answer("pool_id должен быть числом")
        return

    await message.answer(f"⏳ Генерирую отчёт по пулу {pool_id}...")

    # Генерируем и шлём админу
    await ReportService.send_pool_report_to_admin(pool_id=pool_id)


# рабочий
@router.message(FSMSetUserToAdmin.fill_uuid, F.text.contains("Отмена"))
async def cancel(message: Message, state: FSMContext):
    await message.answer(text=f"ОК")
    await state.clear()
