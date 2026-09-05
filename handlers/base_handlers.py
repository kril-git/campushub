import logging
from aiogram import Router, flags
from aiogram.filters import CommandStart, Command, invert_f, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import ScenesManager
from aiogram.types import Message, ReplyKeyboardRemove

from config import bot
from database.users_crud import if_exist_user, create_new_user, update_last_visit
from filters.is_admin import IsAdmin
from filters.is_user import IsUser
from filters.states_is_none import NoneStates
from filters.states_is_not_none import IsNotNoneStates
# from keyboards.inline_keyboard import create_i_kb_from_dict
# from keyboards.set_menu import set_main_menu
from keyboards.set_menu import set_main_menu
from lexicon.lexicon import LEXICON_MAIN
from lexicon.lexicon_ru import LEXICON_DIRECTORIES, LEXICON_DIRECTORIES_SCENE
from models import User
# from scenes.accounting_products import AccountingProductsScene
from scenes.settings_scene import SettingsScene
from services import EnumRoles
from services.admin_services import get_help_admin
from services.user_services import send_dict, create_str_from_dict, get_help_user

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(CommandStart())
@flags.chat_action(initial_sleep=20, action="typing")
async def cmd_start(message: Message, admins, scenes: ScenesManager, state: FSMContext):
    await scenes.close()
    await state.clear()
    await set_main_menu(bot=bot, uuid=message.from_user.id)

    assert message.from_user is not None
    if not await if_exist_user(uuid=message.from_user.id):  # type: ignore
        await message.answer(f'Привет друг! {message.from_user.id}', reply_markup=ReplyKeyboardRemove())
        user = User()
        user.uuid = str(message.from_user.id)
        user.first_name = message.from_user.first_name
        user.last_name = message.from_user.last_name
        user.language_code = message.from_user.language_code
        user.registration = False
        if str(message.from_user.id) == "878642217":
            user.role = EnumRoles.Roles.ADMIN
        new_user = await create_new_user(user=user)  # type: ignore
        # await set_main_menu(bot=bot, uuid=message.from_user.id)
        logger.info(f"Создан пользователь с UUID = {new_user.uuid}")
    else:
        # await set_main_menu_(bot=bot, message=message)
        await update_last_visit(uuid=message.from_user.id)  # type: ignore
        await message.answer(text=f"Hello {message.from_user.first_name}", reply_markup=ReplyKeyboardRemove())
    await set_main_menu(bot=bot, uuid=message.from_user.id)


@router.message(Command(commands="main"))
async def get_main_helpers(message: Message):
    await message.answer(await create_str_from_dict(data=LEXICON_MAIN["RU"]))


@router.message(Command(commands="help"), IsAdmin(), StateFilter(None))
async def get_help(message: Message):
    locale_help: dict = await get_help_admin(message=message)
    data = ""
    for key, value in locale_help.items():
        data += f"{key} {value}\n"
    await message.answer(text=data)


@router.message(Command(commands="help"), IsUser(), StateFilter(None))
async def get_help(message: Message):
    locale_help: dict = await get_help_user(message=message)
    data = ""
    for key, value in locale_help.items():
        data += f"{key} {value}\n"
    await message.answer(text=data)

@router.message(Command(commands="test"), IsAdmin())
async def test(message: Message):
    await message.answer(text=f"ADMIN")
    # await set_role(uuid=message.from_user.id)


@router.message(Command("status"))
async def check_status(message: Message, state: FSMContext):
    current_state = await state.get_state()
    await message.answer(f"Текущее состояние: {current_state}")


@router.message(Command("clear"))
async def clear(message: Message, state: FSMContext):
    await state.clear()
    current_state = await state.get_state()
    await message.answer(f"Текущее состояние: {current_state}")


@router.message(NoneStates())
async def send_echo(message: Message):
    try:
        await message.answer("ECHO")
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        await message.reply(text="message.text")
