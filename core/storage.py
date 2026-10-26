"""
Глобальный FSM storage (Redis).
Вынесено из core/dependencies.py, чтобы избежать циклических импортов.
Инициализируется из AppDependencies после поднятия туннеля.
"""
import logging
from typing import Optional

from redis.asyncio import Redis
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder

logger = logging.getLogger(__name__)


class AppStorage:
    """Класс-контейнер для Redis и FSM storage (classmethod-синглтон)."""

    redis_client: Optional[Redis] = None
    storage: Optional[RedisStorage] = None

    @classmethod
    def setup(cls, redis_client: Redis) -> None:
        """Создаёт RedisStorage. Вызывается из AppDependencies.initialize() после туннеля."""
        cls.redis_client = redis_client
        key_builder = DefaultKeyBuilder(with_bot_id=True, with_destiny=True)
        cls.storage = RedisStorage(
            redis=redis_client,
            key_builder=key_builder,
            state_ttl=60 * 60,          # 1 час
            data_ttl=60 * 60 * 48,      # 48 часов
        )
        logger.info("✅ AppStorage инициализирован")

    @classmethod
    async def close(cls) -> None:
        if cls.storage is not None:
            await cls.storage.close()
            cls.storage = None
        if cls.redis_client is not None:
            await cls.redis_client.close()
            cls.redis_client = None
        logger.info("✅ AppStorage закрыт")

    @classmethod
    def is_ready(cls) -> bool:
        return cls.storage is not None