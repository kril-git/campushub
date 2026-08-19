# dependencies.py
from typing import ClassVar, Optional
from redis.asyncio import Redis
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder

from config import settings
from infrastructure.tunnelmanager import TunnelManager
# from database.helper import db_helper
import logging

from database.db_helper import DatabaseHelper, db_helper

logger = logging.getLogger(__name__)


class AppDependencies:
    """
    Контейнер зависимостей — все атрибуты класса.
    Инициализируется один раз при старте.
    """

    tunnel_manager: ClassVar[Optional[TunnelManager]] = None
    db_helper: ClassVar[DatabaseHelper] = db_helper
    redis_client: ClassVar[Optional[Redis]] = None
    storage: ClassVar[Optional[RedisStorage]] = None
    use_tunnel: ClassVar[bool] = True
    _initialized: ClassVar[bool] = False

    @classmethod
    async def initialize(cls):
        """Инициализация всех зависимостей (вызывается один раз)"""
        if cls._initialized:
            return

        logger.info("🔧 Инициализация зависимостей...")

        if settings.USE_TUNNEL:
            cls.tunnel_manager = TunnelManager(
                ssh_host=settings.DB_HOST_VDS,
                ssh_user=settings.SSH_USERNAME,
                ssh_key_path=settings.SSH_PKEY_PATH,
                ssh_port=settings.SSH_PORT
            )

            await cls.tunnel_manager.forward_port(
                name="postgres",
                local_port=settings.DB_PORT,
                remote_host="localhost",
                remote_port=settings.DB_PORT
            )

            if settings.USE_REDIS:
                await cls.tunnel_manager.forward_port(
                    name="redis",
                    local_port=settings.REDIS_PORT,
                    remote_host="localhost",
                    remote_port=settings.REDIS_PORT
                )

            cls.use_tunnel = True
        else:
            cls.tunnel_manager = None
            cls.use_tunnel = False

        # Redis клиент
        cls.redis_client = await Redis.from_url(url=
                                                f"redis://{settings.get_redis_url}:{str(settings.REDIS_PORT)}",
                                                decode_responses=True
                                                )

        # Redis Storage для FSM
        key_builder = DefaultKeyBuilder(with_bot_id=True, with_destiny=True)
        cls.storage = RedisStorage(
            redis=cls.redis_client,
            key_builder=key_builder,
            state_ttl=60 * 60 * 24,
            data_ttl=60 * 60 * 48,
        )

        cls._initialized = True
        logger.info(f"✅ Зависимости инициализированы {'(туннель)' if cls.use_tunnel else '(локально)'}")

    @classmethod
    async def close(cls):
        """Закрытие всех зависимостей"""
        if not cls._initialized:
            return

        logger.info("🔄 Закрытие зависимостей...")

        if cls.db_helper:
            await cls.db_helper.close()

        if cls.storage:
            await cls.storage.close()

        if cls.redis_client:
            await cls.redis_client.close()

        if cls.tunnel_manager:
            await cls.tunnel_manager.close()

        cls._initialized = False
        logger.info("✅ Все зависимости закрыты")
