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

