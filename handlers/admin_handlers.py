import logging
#
from aiogram import Router, F, flags, types
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import bot
from core.config import settings
from database.admin_crud import get_user_all, set_role, export_users_to_excel, get_personal_record_short
from keyboards.inline_keyboard import create_i_kb_from_dict
from lexicon.lexicon import LEXICON_ADMIN_TEST
from services.EnumQuizStatus import QuizStatus
from services.personal_record_service import get_personal_record_short_lines, get_personal_record_short_lines_render
from database.dao.personal_record_dao import PersonalRecordDAO
from database.users_crud import get_user_by_uuid
from filters.is_admin import IsAdmin
from keyboards.reply_keyboar import r_kb_cancel
from models import User
from services.admin_services import send_users_list_4096, split_into_chunks, send_chunks, split_strings_into_chunks
from services.pool_service import PoolService
from services.quiz_service import QuizService
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


# ==================== Список квизов ====================

@router.callback_query(F.data == "admin:quizzes")
async def on_quizzes_list(callback: CallbackQuery):
    if str(callback.from_user.id) not in settings.ADMINS:
        await callback.answer("Нет доступа", show_alert=True)
        return

    await callback.answer("⏳ Загружаю...")

    quizzes = await QuizService.get_recent(limit=5)

    if not quizzes:
        await callback.message.edit_text(
            "📝 <b>Квизы</b>\n\n"
            "Нет квизов. Загрузите первый через /load_quiz.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📄 Загрузить квиз", callback_data="load_quiz:start")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:menu")],
            ]),
        )
        return

    builder = InlineKeyboardBuilder()
    for quiz in quizzes:
        icon = _quiz_status_icon(quiz.status)
        dates = f"{quiz.start_date:%d.%m}—{quiz.end_date:%d.%m}"
        title = (quiz.title or "")[:30]
        builder.button(
            text=f"{icon} {quiz.id}: {title} ({quiz.status.value}, {dates})",
            callback_data=f"admin:quiz:{quiz.id}",
        )
    builder.adjust(1)

    builder.row(
        InlineKeyboardButton(text="📄 Загрузить квиз", callback_data="load_quiz:start"),
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:menu"),
    )

    await callback.message.edit_text(
        f"📝 <b>Квизы</b> (последние {len(quizzes)}):",
        parse_mode="HTML",
        reply_markup=builder.as_markup(),
    )


def _quiz_status_icon(status: QuizStatus) -> str:
    """Иконка статуса для кнопки."""
    if status == QuizStatus.ACTIVE:
        return "🟢"
    if status == QuizStatus.DRAFT:
        return "⚪"
    if status == QuizStatus.FINISHED:
        return "🔴"
    return "❓"


# ==================== Клик на квиз ====================

@router.callback_query(F.data.startswith("admin:quiz:"))
async def on_quiz_click(callback: CallbackQuery):
    if str(callback.from_user.id) not in settings.ADMINS:
        await callback.answer("Нет доступа", show_alert=True)
        return

    _, _, quiz_id_str = callback.data.split(":")
    try:
        quiz_id = int(quiz_id_str)
    except ValueError:
        await callback.answer("Неверный ID", show_alert=True)
        return

    quiz = await QuizService.get_quiz(quiz_id=quiz_id)
    if not quiz:
        await callback.answer("Квиз не найден", show_alert=True)
        return

    # Действия по статусу
    if quiz.status == QuizStatus.DRAFT:
        # DRAFT → активировать
        await callback.answer(f"⏳ Активирую квиз {quiz_id}...")
        await QuizService.activate_quiz(quiz_id=quiz_id)
        await callback.message.edit_text(
            f"✅ <b>Квиз {quiz_id} активирован</b>\n\n"
            f"Название: {quiz.title}\n"
            f"Период: {quiz.start_date:%d.%m.%Y}—{quiz.end_date:%d.%m.%Y}\n\n"
            f"Теперь можно запустить рассылку.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="🚀 Запустить рассылку",
                    callback_data=f"admin:quiz:send:{quiz_id}",
                )],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:quizzes")],
            ]),
        )

    elif quiz.status == QuizStatus.ACTIVE:
        # ACTIVE → запустить рассылку
        await callback.answer(f"⏳ Запускаю рассылку квиза {quiz_id}...")
        from services.scheduled_jobs import send_quiz_job
        await send_quiz_job(quiz_id=quiz_id)
        await callback.message.edit_text(
            f"✅ <b>Рассылка квиза {quiz_id} запущена</b>\n\n"
            f"Название: {quiz.title}\n"
            f"Период: {quiz.start_date:%d.%m.%Y}—{quiz.end_date:%d.%m.%Y}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:quizzes")],
            ]),
        )

    # elif quiz.status == QuizStatus.FINISHED:
    #     # FINISHED → показать отчёт
    #     await callback.answer(f"⏳ Генерирую отчёт...")
    #     from services.quiz_report_service import QuizReportService
    #     await QuizReportService.send_report_to_admin(quiz_id=quiz_id)
    #     await callback.message.edit_text(
    #         f"✅ <b>Отчёт по квизу {quiz_id} отправлен</b>",
    #         parse_mode="HTML",
    #         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
    #             [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:quizzes")],
    #         ]),
    #     )


# ==================== Кнопка «Назад» в меню ====================

@router.callback_query(F.data == "admin:menu")
async def on_admin_menu(callback: CallbackQuery):
    if str(callback.from_user.id) not in settings.ADMINS:
        await callback.answer("Нет доступа", show_alert=True)
        return

    await callback.answer()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Квизы", callback_data="admin:quizzes")],
        [InlineKeyboardButton(text="📄 Загрузить квиз", callback_data="load_quiz:start")],
        [InlineKeyboardButton(text="📊 Тест отчёта", callback_data="test_report:28")],
    ])
    await callback.message.edit_text(
        "🔧 <b>Админ-панель</b>",
        reply_markup=keyboard,
        parse_mode="HTML",
    )