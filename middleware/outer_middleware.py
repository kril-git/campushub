import logging
from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

import database
from config import settings
# from database.connection import TunnelManager
from core.dependencies import AppDependencies

logger = logging.getLogger(__name__)


class СheckingRoleUser(BaseMiddleware):

    async def __call__(
            self,
            handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: dict[str, Any]
    ) -> Any:
        print("CheckingRoleUser Middleware - зашли в это")
        print(f"{__class__.__name__}, {event.__class__.__name__}")
        logger.debug(
            'Вошли в миддлварь %s, тип события %s',
            __class__.__name__,
            event.__class__.__name__
        )
        tunnel = AppDependencies.tunnel_manager
        # print(database.ssl_connect_kwargs)
        # print("Все ключи в ssl_connect_kwargs:", database.ssl_connect_kwargs.keys())
        await tunnel.connect_ssh()



        # user: User = data.get("event_from_user")
        # print(user.id)
        # print(user.language_code)

        # ...
        # Здесь выполняется код на входе в middleware
        # ...

        result = await handler(event, data)

        # ...
        # Здесь выполняется код на выходе из middleware
        # ...
        # return result, чтобы пропустить апдейт в следующий роутер
        # или
        # просто return, чтобы не пропустить.
        return result
