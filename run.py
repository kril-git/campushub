import asyncio
import logging

from aiogram import Dispatcher
from aiogram.client import bot
from aiogram.fsm.scene import SceneRegistry
from aiogram.fsm.storage.memory import SimpleEventIsolation
from aiogram.fsm.strategy import FSMStrategy
from aiogram.utils.chat_action import ChatActionMiddleware

from config import bot, settings
from config.logger_config import setup_logging
from core.dependencies import AppDependencies
from database.users_crud import get_users_by_role
from middleware.database import SSHHealthMiddleware
from routers import router as main_router, get_scenes
from services.EnumRoles import Roles

logger = logging.getLogger("ceo_helper")


async def main():
    setup_logging()

    # 1. Инициализируем зависимости (один раз)
    await AppDependencies.initialize()
    dp = Dispatcher(
        storage=AppDependencies.storage,
        events_isolation=SimpleEventIsolation(),
        fsm_strategy=FSMStrategy.USER_IN_CHAT
    )

    dp.update.middleware(SSHHealthMiddleware())

    dp.include_router(main_router)
    scenes_registry = SceneRegistry(dp)
    scenes_registry.add(*get_scenes())

    dp.message.middleware(ChatActionMiddleware())
    some_var_1 = 1
    some_var_2 = 'Some text'
    dp['my_int_var'] = some_var_1
    dp['my_text_var'] = some_var_2
    settings.ADMINS = await get_users_by_role(role=Roles.ADMIN.name)  # type: ignore

    dp["admins"] = settings.ADMINS
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")
        logger.error(f"Что-то не так")
