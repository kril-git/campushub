import logging

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from core.config import settings

logger = logging.getLogger(__name__)


class DatabaseHelperLocal:
    def __init__(self):
        self.engine = create_async_engine(
            url=settings.DATABASE_URL, echo=settings.DB_ECHO
        )

        self.session_factory = async_sessionmaker(
            bind=self.engine, autoflush=False, autocommit=False, expire_on_commit=False
        )


class DatabaseHelperVPS:
    def __init__(self):
        self.engine = create_async_engine(
            url=settings.database_url_vds_server,
            echo=settings.DB_ECHO
        )

        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False
        )


class DatabaseHelper:
    """
    Класс DatabaseHelper.
    Создаёт движок и сессию.
    Если settings.VPS = TRUE, то класс создаст подключение к VPS серверу,
    иначе к локальному.
    """
    def __init__(self):
        if settings.USE_TUNNEL:
            self.engine = create_async_engine(
                url=settings.database_url_vds_server,
                echo=settings.DB_ECHO,
                pool_pre_ping=True,   # ← главное
                pool_recycle=300

            )

            self.session_factory = async_sessionmaker(
                bind=self.engine,
                autoflush=False,
                autocommit=False,
                expire_on_commit=False
            )
        else:
            self.engine = create_async_engine(
                url=settings.DATABASE_URL, echo=settings.DB_ECHO
            )

            self.session_factory = async_sessionmaker(
                bind=self.engine,
                autoflush=False,
                autocommit=False,
                expire_on_commit=False
            )

    async def close(self):
        if self.engine:
            await self.engine.dispose()
            logger.info("DatabaseHelper закрыт")


db_helper = DatabaseHelper()
