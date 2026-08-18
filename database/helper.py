# database_helper.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from config import settings
import logging

logger = logging.getLogger(__name__)


class DatabaseHelper:
    def __init__(self):
        self.engine = create_async_engine(
            url=settings.DATABASE_URL,
            echo=settings.DB_ECHO,
            pool_pre_ping=True,
            pool_recycle=300
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False
        )
        logger.info("✅ DatabaseHelper инициализирован")

    async def recreate_engine(self):
        """Пересоздаёт engine после восстановления соединения"""
        logger.info(f"🔄 Пересоздаю engine...{__name__}")
        if self.engine:
            await self.engine.dispose()

        self.engine = create_async_engine(
            url=settings.database_url,
            echo=settings.DB_ECHO,
            pool_pre_ping=True,
            pool_recycle=300
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False
        )
        logger.info("✅ Engine пересоздан")

    async def health_check(self) -> bool:
        if not self.engine:
            return False
        try:
            async with self.engine.begin() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception:
            return False

    async def close(self):
        if self.engine:
            await self.engine.dispose()
            logger.info("DatabaseHelper закрыт")


# Создаём глобальный экземпляр (он использует settings.database_url)
db_helper = DatabaseHelper()