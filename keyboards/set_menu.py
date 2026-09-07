from aiogram import Bot
from aiogram.types import BotCommand, Message

from config import settings
from lexicon.lexicon_ru import LEXICON_MENU_ADMIN_CAMPUSHUB, LEXICON_MENU_USER_CAMPUSHUB
from services.admin_services import _is_admin


async def set_main_menu(bot: Bot, uuid: int | str):

    if await _is_admin(uuid=uuid):
        lexicon_menu = LEXICON_MENU_ADMIN_CAMPUSHUB
    else:
        lexicon_menu = LEXICON_MENU_USER_CAMPUSHUB

    main_menu_commands = [
        BotCommand(command=command,
                   description=description
                   ) for command, description in lexicon_menu.items()
    ]
    await bot.set_my_commands(main_menu_commands)

