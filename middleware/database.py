import logging
import asyncpg
import asyncssh
from aiogram import BaseMiddleware
from core.dependencies import AppDependencies

logger = logging.getLogger(__name__)


class SSHHealthMiddleware(BaseMiddleware):
    """
    Middleware, который НЕ проверяет SSH активно.
    Только реагирует на исключения, если они возникли.
    """

    async def __call__(self, handler, event, data):
        # Если туннель не используется — просто пропускаем
        if not AppDependencies.use_tunnel:
            return await handler(event, data)

        try:
            # Пытаемся выполнить хендлер
            return await handler(event, data)

        except (asyncssh.Error, asyncpg.exceptions.ConnectionDoesNotExistError) as e:
            # Ловим ошибки SSH или БД
            logger.warning(f"⚠️ Ошибка соединения: {e}")
            tunnel_manager = AppDependencies.tunnel_manager

            if tunnel_manager:
                try:
                    # Переподключаем туннель
                    await tunnel_manager.reconnect()
                    logger.info("✅ Туннель переподключён")
                    # Повторяем запрос (опционально)
                    return await handler(event, data)
                except Exception as reconnect_error:
                    logger.error(f"❌ Не удалось переподключить туннель: {reconnect_error}")
                    await event.message.answer(
                        "⚠️ *Сервис временно недоступен*\nПожалуйста, попробуйте позже.",
                        parse_mode="Markdown"
                    )
                    return
            else:
                # Если туннель отсутствует, просто пробрасываем ошибку
                raise


