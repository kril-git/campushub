import asyncio
import logging
from functools import wraps
from typing import ParamSpec, TypeVar, Callable, Awaitable, Optional

import asyncpg
import asyncssh
import redis
from aiogram import Dispatcher
from aiogram.exceptions import TelegramNetworkError

from core.config import settings
from database.db_helper import db_helper

logger = logging.getLogger(__name__)

P = ParamSpec("P")  # 👈 P - это "параметры функции"
T = TypeVar("T")  # T - это "любой тип, но один и тот же во всей функции"


# def connection(method):
#     @wraps(method)  # 👈 Копирует метаданные из method в wrapper
#     async def wrapper(*args, **kwargs):
#         async with db_helper.session_factory() as session:
#             try:
#                 return await method(*args, session=session, **kwargs)
#             except Exception as e:
#                 await session.rollback()
#                 logger.error(e)
#                 raise e
#             except TelegramNetworkError as e:
#                 logger.error(f"TelegramNetworkError в модуле connection.py")
#                 print(f"TelegramNetworkError в модуле connection.py")
#             finally:
#                 await session.close()
#
#     return wrapper


def connection(method: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
    """
    Callable — это способ сказать типизатору:
    "Эта переменная/параметр является функцией,
    и она принимает такие-то аргументы и возвращает такой-то тип".
    Синтаксис -> Callable[[типы_аргументов], возвращаемый_тип]

    По шагам:

    method — это функция (наш метод БД)
    Callable[P, Awaitable[T]] — method принимает параметры P и возвращает Awaitable[T]
    Декоратор возвращает функцию с теми же параметрами P, которая тоже возвращает Awaitable[T]
    Это гарантирует, что сигнатура метода не изменилась после обёртки

    Awaitable — это "обещание" получить значение типа T в будущем. Асинхронная функция (async def)

    Это означает:

    method — это асинхронная функция, которая возвращает Awaitable[T]
    Декоратор возвращает функцию с той же сигнатурой — тоже асинхронную.
    То есть, ваш декоратор работает только с async def функциями.

    Ключевые выводы:

    P (ParamSpec) - захватывает параметры функции (args/kwargs)
    T (TypeVar) - тип возвращаемого значения после await
    Awaitable[T] - асинхронный объект, возвращающий T
    Callable[[P], Awaitable[T]] - асинхронная функция с параметрами P
    -> Callable[P, Awaitable[T]] - возвращает функцию с теми же параметрами
    Такая сигнатура сохраняет типы при декорировании
    Это идеальный паттерн для декораторов асинхронных функций (БД, API, сетевые запросы),
    где нужно добавить логику управления соединениями без потери информации о типах!


    """

    @wraps(method)  # 👈 Копирует метаданные из method в wrapper
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        async with db_helper.session_factory() as session:
            try:
                return await method(*args, session=session, **kwargs)
            except TelegramNetworkError as e:
                logger.error(f"TelegramNetworkError в модуле connection.py {method.__name__}: {e}")
            except Exception as e:
                await session.rollback()
                logger.exception(f"Ошибка бд в {method.__name__}: {type(e).__name__}: {e}")
                raise

    return wrapper


#
# def connection(method):
#     async def wrapper(*args, **kwargs):
#         if settings.VPS:
#             with SSH(hostname=settings.DB_HOST_VDS,
#                      username=settings.SSH_USERNAME,
#                      password=settings.SSH_PASSWORD,
#                      pkey=settings.SSH_PKEY_PATH,
#                      port=22) as ssh:  # noob@10.0.1.**
#                 # out = ssh.exec_cmd('ls -al /var')
#                 # print(out)
#                 # pass
#                 async with db_helper.session_factory() as session:
#                     try:
#                         return await method(*args, session=session, **kwargs)
#                     except Exception as e:
#                         await session.rollback()
#                         logger.error(e)
#                         raise e
#                     finally:
#                         await session.close()
#
#     return wrapper


# class AsyncTunnelManager:
#     """
#     Менеджер для асинхронных SSH-туннелей через asyncssh.
#     Полностью не блокирует event loop.
#     """
#
#     def __init__(self):
#         self.postgres_connection: asyncssh.SSHClientConnection | None = None
#         self.postgres_listener: asyncio.Server | None = None
#
#         self.redis_connection: asyncssh.SSHClientConnection | None = None
#         self.redis_listener: asyncio.Server | None = None
#
#     @staticmethod
#     async def _create_tunnel(
#             remote_port: int,
#             remote_host: str,
#             local_port: int,
#             local_host: str = "127.0.0.1",
#             name: str = "unknown",
#     ) -> tuple[asyncssh.SSHClientConnection, asyncio.Server]:
#         # --- НАСТРОЙКА KEEPALIVE ДЛЯ НАДЕЖНОСТИ ---
#         # keepalive_interval: посылать keepalive пакеты каждые 30 секунд
#         # keepalive_count_max: если 3 пакета подряд не получили ответ, разрываем соединение
#         ssh_options = asyncssh.SSHClientConnectionOptions(
#             keepalive_interval=30,  # <-- Главный герой!
#             keepalive_count_max=3
#         )
#         # -----------------------------------------
#         connect_kwargs = {
#             "host": settings.DB_HOST_VDS,
#             "port": settings.SSH_PORT,
#             "username": settings.SSH_USERNAME,
#         }
#         # Аутентификация: ключ или пароль
#         if settings.SSH_PKEY_PATH:
#             connect_kwargs["client_keys"] = [settings.SSH_PKEY_PATH]
#         elif settings.SSH_PASSWORD:
#             connect_kwargs["password"] = settings.SSH_PASSWORD
#         else:
#             raise ValueError("Не предоставлен ни ключ ни пароль")
#
#         # Устанавливаем SSH соединение
#         logger.info(f"Establishing SSH connection for {name} to {settings.DB_HOST_VDS}:{settings.SSH_PORT}")
#         ssh_connection = await asyncssh.connect(**connect_kwargs)
#         logger.info(f"SSH connection established for {name}")
#
#         # Создаём локальный порт-форвардинг (туннель)
#         # forward_local_port(listen_host, listen_port, dest_host, dest_port)
#         listener = await ssh_connection.forward_local_port(
#             local_host,  # на каком интерфейсе слушаем локально
#             local_port,  # на каком порту слушаем локально
#             remote_host,  # куда направлять трафик на удалённой стороне
#             remote_port  # на какой порт на удалённой стороне
#         )
#         logger.info(f"Tunnel for {name} created: {local_host}:{local_port} -> remote:{remote_port}")
#         return ssh_connection, listener
#
#     async def init_postgres_tunnel(self) -> bool:
#         """Инициализирует асинхронный туннель для PostgreSQL"""
#         try:
#             self.postgres_connection, self.postgres_listener = await self._create_tunnel(
#                 remote_port=settings.PG_PORT,
#                 remote_host=settings.LOCALHOST,
#                 local_port=settings.PG_PORT,
#                 local_host="0.0.0.0",  # Доступно для других контейнеров
#                 name="PostgreSQL"
#             )
#             logger.info("✅ SSH tunnel for PostgreSQL established successfully")
#             return True
#         except asyncssh.Error as e:
#             logger.error(f"❌ SSH error for PostgreSQL tunnel: {e}")
#             return False
#         except Exception as e:
#             logger.error(f"❌ Unexpected error for PostgreSQL tunnel: {e}")
#             return False
#
#     async def init_redis_tunnel(self) -> bool:
#         """Инициализирует асинхронный туннель для Redis"""
#         try:
#             self.redis_connection, self.redis_listener = await self._create_tunnel(
#                 remote_port=settings.REDIS_PORT,
#                 remote_host=settings.LOCALHOST,
#                 local_port=settings.REDIS_PORT,
#                 local_host="127.0.0.1",
#                 name="Redis"
#             )
#             logger.info("✅ SSH tunnel for Redis established successfully")
#             return True
#         except asyncssh.Error as e:
#             logger.error(f"❌ SSH error for Redis tunnel: {e}")
#             return False
#         except Exception as e:
#             logger.error(f"❌ Unexpected error for Redis tunnel: {e}")
#             return False
#
#     async def close_tunnels(self):
#         """Закрывает все туннели асинхронно"""
#         # Закрываем PostgreSQL туннель
#         if self.postgres_listener:
#             self.postgres_listener.close()
#             await self.postgres_listener.wait_closed()
#             logger.info("PostgreSQL tunnel listener closed")
#
#         if self.postgres_connection:
#             self.postgres_connection.close()
#             await self.postgres_connection.wait_closed()
#             logger.info("PostgreSQL SSH connection closed")
#
#         # Закрываем Redis туннель
#         if self.redis_listener:
#             self.redis_listener.close()
#             await self.redis_listener.wait_closed()
#             logger.info("Redis tunnel listener closed")
#
#         if self.redis_connection:
#             self.redis_connection.close()
#             await self.redis_connection.wait_closed()
#             logger.info("Redis SSH connection closed")
#
#     @property
#     def is_healthy(self) -> bool:
#         """Проверяет состояние туннелей"""
#         postgres_ok = (
#                 self.postgres_connection and
#                 not self.postgres_connection.is_closed()
#         )
#         redis_ok = (
#                 self.redis_connection and
#                 not self.redis_connection.is_closed()
#         )
#         return postgres_ok and redis_ok

# class AsyncTunnelManager:
#     def __init__(self):
#         self.postgres_connection: Optional[asyncssh.SSHClientConnection] = None
#         self.redis_connection: Optional[asyncssh.SSHClientConnection] = None
#
#     @staticmethod
#     async def _create_connection(name: str) -> asyncssh.SSHClientConnection:
#         """Создает и возвращает SSH-соединение с правильными опциями."""
#         # 1. Готовим параметры подключения
#         connect_kwargs = {
#             "host": settings.DB_HOST_VDS,
#             "port": settings.SSH_PORT,
#             "username": settings.SSH_USERNAME,
#             # Keepalive через распаковку словаря — самый надежный способ [citation:1]
#             "keepalive_interval": 30,
#             "keepalive_count_max": 3,
#         }
#
#         # 2. Аутентификация
#         if settings.SSH_PKEY_PATH:
#             connect_kwargs["client_keys"] = [settings.SSH_PKEY_PATH]
#         elif settings.SSH_PASSWORD:
#             connect_kwargs["password"] = settings.SSH_PASSWORD
#         else:
#             raise ValueError("Neither SSH key nor password provided")
#
#         logger.info(f"Establishing SSH connection for {name}")
#         # Передаем параметры напрямую, без options=...
#         connection = await asyncssh.connect(**connect_kwargs)
#         logger.info(f"SSH connection established for {name}")
#         return connection
#
#     async def init_postgres_tunnel(self) -> bool:
#         try:
#             # 1. Создаем соединение
#             self.postgres_connection = await self._create_connection("PostgreSQL")
#
#             # 2. Создаем туннель
#             # (Постгресу нужен '0.0.0.0' для доступа извне, если бот в контейнере)
#             listener = await self.postgres_connection.forward_local_port(
#                 "0.0.0.0", settings.PG_PORT,
#                 "127.0.0.1", settings.PG_PORT
#             )
#             logger.info("✅ PostgreSQL tunnel established")
#
#             # Запускаем фоновую задачу, которая просто ждет закрытия соединения.
#             # Это более надежно, чем wait_closed() на listener'е, особенно на Python 3.12+ [citation:3].
#             asyncio.create_task(self._wait_for_connection_close(self.postgres_connection, "PostgreSQL"))
#             return True
#
#         except Exception as e:
#             logger.error(f"❌ PostgreSQL tunnel failed: {e}")
#             return False
#
#     async def init_redis_tunnel(self) -> bool:
#         try:
#             self.redis_connection = await self._create_connection("Redis")
#
#             listener = await self.redis_connection.forward_local_port(
#                 "127.0.0.1", settings.REDIS_PORT,
#                 "127.0.0.1", settings.REDIS_PORT
#             )
#             logger.info("✅ Redis tunnel established")
#
#             asyncio.create_task(self._wait_for_connection_close(self.redis_connection, "Redis"))
#             return True
#
#         except Exception as e:
#             logger.error(f"❌ Redis tunnel failed: {e}")
#             return False
#
#     async def _wait_for_connection_close(self, connection: asyncssh.SSHClientConnection, name: str):
#         """Фоновая задача, которая следит за здоровьем туннеля."""
#         try:
#             # Ждем, пока соединение не будет закрыто (прозрачно для нас)
#             await connection.wait_closed()
#             logger.warning(f"⚠️ SSH connection for {name} was closed unexpectedly!")
#         except Exception as e:
#             logger.error(f"Error while waiting for connection {name}: {e}")
#
#     async def close_tunnels(self):
#         """Корректно завершает все туннели."""
#         logger.info("Closing SSH tunnels...")
#         if self.redis_connection:
#             self.redis_connection.close()
#             await self.redis_connection.wait_closed()
#         if self.postgres_connection:
#             self.postgres_connection.close()
#             await self.postgres_connection.wait_closed()
#         logger.info("All SSH tunnels closed.")
#
#     @property
#     def is_healthy(self) -> bool:
#         """Проверка, живы ли еще соединения."""
#         redis_ok = self.redis_connection and not self.redis_connection.is_closed()
#         postgres_ok = self.postgres_connection and not self.postgres_connection.is_closed()
#         return redis_ok and postgres_ok
#
#
# tunnel_manager = AsyncTunnelManager()
#
# def retry_on_failure(max_attempts: int = 5, delay: float = 2.0, backoff: float = 2.0):
#     """
#     Декоратор для автоматического повторения операции при ошибке.
#
#     Args:
#         max_attempts: Максимальное количество попыток
#         delay: Начальная задержка между попытками (секунды)
#         backoff: Множитель для увеличения задержки (экспоненциальная выдержка)
#     """
#
#     def decorator(func: Callable) -> Callable:
#         @wraps(func)
#         async def wrapper(*args, **kwargs):
#             current_delay = delay
#             last_exception = None
#
#             for attempt in range(1, max_attempts + 1):
#                 try:
#                     return await func(*args, **kwargs)
#                 except Exception as e:
#                     last_exception = e
#                     if attempt == max_attempts:
#                         logger.error(f"Operation failed after {max_attempts} attempts: {e}")
#                         raise
#
#                     logger.warning(
#                         f"Attempt {attempt}/{max_attempts} failed: {e}. "
#                         f"Retrying in {current_delay}s..."
#                     )
#                     await asyncio.sleep(current_delay)
#                     current_delay *= backoff
#
#             raise last_exception
#
#         return wrapper
#
#     return decorator
#
#
# class AsyncTunnelManager:
#     """
#     Менеджер для асинхронных SSH-туннелей с автоматическим переподключением.
#
#     Особенности:
#     - Автоматическое восстановление туннеля при обрыве связи
#     - Мониторинг состояния соединения
#     - Экспоненциальная задержка при повторных попытках
#     """
#
#     def __init__(self):
#         self._redis_connection: Optional[asyncssh.SSHClientConnection] = None
#         self._postgres_connection: Optional[asyncssh.SSHClientConnection] = None
#
#         self._redis_listener: Optional[asyncssh.SSHListener] = None
#         self._postgres_listener: Optional[asyncssh.SSHListener] = None
#
#         self._redis_monitor_task: Optional[asyncio.Task] = None
#         self._postgres_monitor_task: Optional[asyncio.Task] = None
#
#         self._redis_connected = asyncio.Event()
#         self._postgres_connected = asyncio.Event()
#
#         self._shutdown = False
#
#     @staticmethod
#     async def _create_connection(
#             name: str,
#             remote_host: str,
#             remote_port: int,
#     ) -> asyncssh.SSHClientConnection:
#         """
#         Создаёт SSH-соединение с правильными настройками.
#
#         Keepalive настроен на уровне клиента [citation:3].
#         """
#         connect_kwargs = {
#             "host": settings.DB_HOST_VDS,
#             "port": settings.SSH_PORT,
#             "username": settings.SSH_USERNAME,
#             "keepalive_interval": 30,
#             "keepalive_count_max": 3,
#             "known_hosts": None,  # Для разработки, в проде используйте known_hosts
#         }
#
#         if settings.SSH_PKEY_PATH:
#             connect_kwargs["client_keys"] = [settings.SSH_PKEY_PATH]
#         elif settings.SSH_PASSWORD:
#             connect_kwargs["password"] = settings.SSH_PASSWORD
#         else:
#             raise ValueError("Neither SSH key nor password provided")
#
#         logger.info(f"Establishing SSH connection for {name}")
#         connection = await asyncssh.connect(**connect_kwargs)
#         logger.info(f"SSH connection established for {name}")
#         return connection
#
#     @retry_on_failure(max_attempts=3, delay=1.0)
#     async def _create_tunnel(
#             self,
#             name: str,
#             remote_host: str,
#             remote_port: int,
#             local_host: str,
#             local_port: int,
#     ) -> asyncssh.SSHListener:
#         """
#         Создаёт туннель с автоматическим повтором при ошибке.
#         """
#         connection = await self._create_connection(name, remote_host, remote_port)
#
#         listener = await connection.forward_local_port(
#             local_host, local_port,
#             remote_host, remote_port
#         )
#
#         logger.info(f"Tunnel for {name}: {local_host}:{local_port} -> {remote_host}:{remote_port}")
#
#         # Сохраняем соединение в зависимости от типа
#         if name == "PostgreSQL":
#             self._postgres_connection = connection
#             self._postgres_listener = listener
#         else:
#             self._redis_connection = connection
#             self._redis_listener = listener
#
#         return listener
#
#     async def _monitor_connection(
#             self,
#             name: str,
#             connection: asyncssh.SSHClientConnection,
#             connected_event: asyncio.Event,
#             reconnect_callback: Callable[[], Awaitable[None]]
#     ):
#         """
#         Мониторит состояние соединения и инициирует переподключение при обрыве.
#
#         Использует connection.wait_closed() вместо listener.wait_closed(),
#         так как это более надёжно на Python 3.12+ [citation:4].
#         """
#         try:
#             # Ждём, пока соединение не будет закрыто
#             await connection.wait_closed()
#
#             if not self._shutdown:
#                 logger.warning(f"⚠️ Connection for {name} was closed unexpectedly!")
#                 connected_event.clear()
#                 await reconnect_callback()
#         except asyncio.CancelledError:
#             logger.info(f"Monitor task for {name} cancelled")
#             raise
#         except Exception as e:
#             logger.error(f"Error monitoring {name} connection: {e}")
#             if not self._shutdown:
#                 connected_event.clear()
#                 await reconnect_callback()
#
#     async def _reconnect_tunnel(self, name: str, tunnel_type: str):
#         """
#         Переподключает упавший туннель с экспоненциальной задержкой.
#         """
#         delay = 1
#         max_delay = 60
#
#         while not self._shutdown:
#             try:
#                 logger.info(f"Attempting to reconnect {name} tunnel...")
#
#                 if tunnel_type == "postgres":
#                     await self._create_tunnel(
#                         name, "127.0.0.1", settings.PG_PORT,
#                         "0.0.0.0", settings.PG_PORT
#                     )
#                 else:
#                     await self._create_tunnel(
#                         name, "127.0.0.1", settings.REDIS_PORT,
#                         "127.0.0.1", settings.REDIS_PORT
#                     )
#
#                 # Успешно переподключились
#                 logger.info(f"✅ {name} tunnel reconnected successfully")
#
#                 if tunnel_type == "postgres":
#                     self._postgres_connected.set()
#                 else:
#                     self._redis_connected.set()
#
#                 # Запускаем новый мониторинг
#                 if tunnel_type == "postgres" and self._postgres_connection:
#                     self._postgres_monitor_task = asyncio.create_task(
#                         self._monitor_connection(
#                             name,
#                             self._postgres_connection,
#                             self._postgres_connected,
#                             lambda: self._reconnect_tunnel(name, "postgres")
#                         )
#                     )
#                 elif tunnel_type == "redis" and self._redis_connection:
#                     self._redis_monitor_task = asyncio.create_task(
#                         self._monitor_connection(
#                             name,
#                             self._redis_connection,
#                             self._redis_connected,
#                             lambda: self._reconnect_tunnel(name, "redis")
#                         )
#                     )
#
#                 return
#
#             except Exception as e:
#                 logger.error(f"Reconnection attempt failed for {name}: {e}")
#
#                 if delay < max_delay:
#                     delay = min(delay * 2, max_delay)
#
#                 logger.info(f"Waiting {delay}s before next reconnection attempt...")
#                 await asyncio.sleep(delay)
#
#     async def init_postgres_tunnel(self) -> bool:
#         """Инициализирует туннель для PostgreSQL с мониторингом"""
#         try:
#             await self._create_tunnel(
#                 "PostgreSQL", "127.0.0.1", settings.PG_PORT,
#                 "0.0.0.0", settings.PG_PORT
#             )
#
#             self._postgres_connected.set()
#
#             # Запускаем фоновый мониторинг
#             self._postgres_monitor_task = asyncio.create_task(
#                 self._monitor_connection(
#                     "PostgreSQL",
#                     self._postgres_connection,
#                     self._postgres_connected,
#                     lambda: self._reconnect_tunnel("PostgreSQL", "postgres")
#                 )
#             )
#
#             logger.info("✅ PostgreSQL tunnel established with auto-reconnect")
#             return True
#
#         except Exception as e:
#             logger.error(f"❌ PostgreSQL tunnel initialization failed: {e}")
#             return False
#
#     async def init_redis_tunnel(self) -> bool:
#         """Инициализирует туннель для Redis с мониторингом"""
#         try:
#             await self._create_tunnel(
#                 "Redis", "127.0.0.1", settings.REDIS_PORT,
#                 "127.0.0.1", settings.REDIS_PORT
#             )
#
#             self._redis_connected.set()
#
#             # Запускаем фоновый мониторинг
#             self._redis_monitor_task = asyncio.create_task(
#                 self._monitor_connection(
#                     "Redis",
#                     self._redis_connection,
#                     self._redis_connected,
#                     lambda: self._reconnect_tunnel("Redis", "redis")
#                 )
#             )
#
#             logger.info("✅ Redis tunnel established with auto-reconnect")
#             return True
#
#         except Exception as e:
#             logger.error(f"❌ Redis tunnel initialization failed: {e}")
#             return False
#
#     async def wait_for_postgres(self, timeout: float = 30.0) -> bool:
#         """Ожидает, пока PostgreSQL туннель не станет доступен"""
#         try:
#             await asyncio.wait_for(self._postgres_connected.wait(), timeout)
#             return True
#         except asyncio.TimeoutError:
#             logger.error("Timeout waiting for PostgreSQL tunnel")
#             return False
#
#     async def wait_for_redis(self, timeout: float = 30.0) -> bool:
#         """Ожидает, пока Redis туннель не станет доступен"""
#         try:
#             await asyncio.wait_for(self._redis_connected.wait(), timeout)
#             return True
#         except asyncio.TimeoutError:
#             logger.error("Timeout waiting for Redis tunnel")
#             return False
#
#     async def close_tunnels(self):
#         """Корректно завершает все туннели и мониторы"""
#         logger.info("Closing SSH tunnels...")
#         self._shutdown = True
#
#         # Отменяем задачи мониторинга
#         if self._postgres_monitor_task:
#             self._postgres_monitor_task.cancel()
#             try:
#                 await self._postgres_monitor_task
#             except asyncio.CancelledError:
#                 pass
#
#         if self._redis_monitor_task:
#             self._redis_monitor_task.cancel()
#             try:
#                 await self._redis_monitor_task
#             except asyncio.CancelledError:
#                 pass
#
#         # Закрываем соединения
#         if self._redis_connection:
#             self._redis_connection.close()
#             await self._redis_connection.wait_closed()
#         if self._postgres_connection:
#             self._postgres_connection.close()
#             await self._postgres_connection.wait_closed()
#
#         logger.info("All SSH tunnels closed.")
#
#     @property
#     def is_healthy(self) -> bool:
#         """Проверяет, активны ли туннели"""
#         redis_ok = self._redis_connection and not self._redis_connection.is_closed()
#         postgres_ok = self._postgres_connection and not self._postgres_connection.is_closed()
#         return redis_ok and postgres_ok
#
#
# # Глобальный экземпляр
# tunnel_manager = AsyncTunnelManager()
#
#
# async def on_startup(dispatcher: Dispatcher):
#     """Вызывается при старте бота"""
#     logger.info("Starting bot and establishing SSH tunnels...")
#
#     # Запускаем оба туннеля параллельно
#     postgres_task = asyncio.create_task(tunnel_manager.init_postgres_tunnel())
#     redis_task = asyncio.create_task(tunnel_manager.init_redis_tunnel())
#
#     # Ждём их готовности
#     postgres_ok, redis_ok = await asyncio.gather(
#         tunnel_manager.wait_for_postgres(),
#         tunnel_manager.wait_for_redis()
#     )
#
#     if not (postgres_ok and redis_ok):
#         logger.error("Failed to establish required tunnels!")
#         raise RuntimeError("SSH tunnels initialization failed")
#
#     logger.info("✅ Bot is ready with auto-reconnecting SSH tunnels!")
#
#
# async def on_shutdown(dispatcher: Dispatcher):
#     """Вызывается при остановке бота"""
#     logger.info("Shutting down...")
#     await tunnel_manager.close_tunnels()
#
#
# # async def init_tunnels() -> bool:
# #     """
# #     Инициализирует все SSH туннели (запускать при старте бота)
# #     """
# #     logger.info("🔄 Initializing SSH tunnels...")
# #
# #     # Инициализируем оба туннеля параллельно для скорости
# #     postgres_task = asyncio.create_task(tunnel_manager.init_postgres_tunnel())
# #     redis_task = asyncio.create_task(tunnel_manager.init_redis_tunnel())
# #
# #     postgres_ok, redis_ok = await asyncio.gather(postgres_task, redis_task)
# #
# #     if postgres_ok and redis_ok:
# #         logger.info("✅ All SSH tunnels established successfully")
# #         return True
# #     else:
# #         logger.warning(f"⚠️ Tunnels status - PostgreSQL: {postgres_ok}, Redis: {redis_ok}")
# #         return False
# #
# #
# # async def close_tunnels():
# #     """
# #     Закрывает все SSH туннели (запускать при остановке бота)
# #     """
# #     logger.info = "🔄 Closing SSH tunnels..."
# #     await tunnel_manager.close_tunnels()
# #     logger.info = "✅ All SSH tunnels closed"
# #
# #
# # async def on_startup(dispatcher: Dispatcher):
# #     """Вызывается при старте бота"""
# #     logger.info = "🚀 Bot starting up..."
# #
# #     if not await init_tunnels():
# #         logger.error("❌ Failed to establish SSH tunnels! Bot cannot continue.")
# #         raise RuntimeError("SSH tunnels initialization failed")
# #
# #     logger.info = "✅ Bot is ready with SSH tunnels!"
#
#
# # async def on_shutdown(dispatcher: Dispatcher):
# #     """Вызывается при остановке бота"""
# #     logger.info = "🛑 Bot shutting down..."
# #     await close_tunnels()
# #     logger.info = "👋 Goodbye!"
#
#
# # async def postgres_tunnel_init() -> bool:
# #     """
# #     Инициализирует POSTGRES для работы через SSH туннель.
# #     set_keepalive=0.0 -> для того, что бы туннель не отключился.
# #     """
# #
# #     with SSHTunnelForwarder(
# #             ssh_address_or_host=(settings.DB_HOST_VDS, settings.SSH_PORT),
# #             ssh_username=settings.SSH_USERNAME,
# #             ssh_password=settings.SSH_PASSWORD,
# #             ssh_pkey=settings.SSH_PKEY_PATH,
# #             ssh_config_file=None,
# #             remote_bind_address=(settings.LOCALHOST, settings.PG_PORT),
# #             # local_bind_address=(settings.LOCALHOST, settings.PG_PORT),
# #             local_bind_address=("0.0.0.0", settings.PG_PORT),
# #             allow_agent=False,
# #             set_keepalive=30, ) as tunnel:
# #         logging.info(f"SSH tunnel for POSTGRES established. Local port: {tunnel.local_bind_address[1]}")
# #     tunnel.start()
# #     if tunnel.is_active:
# #         return True
# #     else:
# #         return False
# #
# #
# # async def redis_tunnel_init() -> bool:
# #     """
# #     Инициализирует REDIS для работы через SSH туннель.
# #     set_keepalive=0.0 -> для того, что бы туннель не отключился.
# #     """
# #     with SSHTunnelForwarder(
# #             ssh_address_or_host=(settings.DB_HOST_VDS, settings.SSH_PORT),
# #             ssh_username=settings.SSH_USERNAME,
# #             ssh_password=settings.SSH_PASSWORD,
# #             ssh_pkey=settings.SSH_PKEY_PATH,
# #             ssh_config_file=None,
# #             remote_bind_address=(settings.LOCALHOST, settings.REDIS_PORT),
# #             local_bind_address=(settings.LOCALHOST, settings.REDIS_PORT),
# #             allow_agent=False,
# #             # set_keepalive=0.0
# #             set_keepalive=30) as tunnel:
# #         logging.info(f"SSH tunnel established. Local port: {tunnel.local_bind_address[1]}")
# #     tunnel.start()
# #     if tunnel.is_active:
# #         return True
# #     else:
# #         return False
# #
# #
# # async def init_tunnel():
# #     redis: bool = False
# #     postgres: bool = False
# #     # with SSH(hostname=settings.DB_HOST_VDS,
# #     #          username=settings.SSH_USERNAME,
# #     #          password=settings.SSH_PASSWORD,
# #     #          pkey=settings.SSH_PKEY_PATH,
# #     #          port=22) as ssh:  # noob@10.0.1.**
# #     #     pass
# #
# #     try:
# #         if await postgres_tunnel_init():
# #             logger.info(f"SSH туннель для сервера БД поднялся успешно")
# #             postgres = True
# #     except Exception as e:
# #         logger.info(f"SSH туннель не работает, ошибка {e}")
# #     try:
# #         if await redis_tunnel_init():
# #             logger.info(f"SSH туннель для сервера REDIS поднялся успешно")
# #             redis = True
# #     except Exception as e:
# #         logger.info(f"SSH туннель не работает, ошибка {e}")
# #
# #     if redis & postgres:
# #         return True
# #     else:
# #         return False
#
# class TunnelManager:
#
#     def __init__(self, ssl_config):
#         self.ssl_config = ssl_config
#         self.conn: asyncssh.SSHClientConnection | None = None
#         self.tunnels = []
#         self._lock = asyncio.Lock()
#
#         # Клиенты для БД
#         self.postgres_pool: asyncpg.Pool | None
#         self.redis_client: redis.Redis | None
#
#     async def connect_ssh(self):
#         """Устанавливаем SSH соединение"""
#         async with self._lock:
#             if self.conn and not self.conn.is_closed():
#                 return self.conn
#
#             # print(f"🔌 Подключаюсь к SSH серверу {self.ssl_config.get("host")}...")
#             self.conn = await asyncssh.connect(
#                 **self.ssl_config
#             )
#             print("✅ SSH соединение установлено")
#             return self.conn
