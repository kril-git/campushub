# services/scheduled_jobs.py
import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import settings
# from core.dependencies import AppDependencies
from database.dao.pool_dao import DAOPools
from services.EnumPools import PoolCategory
from services.sending_service import send_message_text_to_user

logger = logging.getLogger(__name__)


async def daily_pool_job(test_users: list[int] | None = None) -> None:
    """
    Ежедневная задача 09:00 по Минску.

    test_users=None  → боевой режим, рассылка всем пользователям
    test_users=[...] → тестовый режим, только этим ID
    """
    # tz = AppDependencies.tz
    # today = datetime.now(tz).date()
    logger.info("🔔 daily_pool_job start")

    #     Получаем активный пул если существует
    active_pool = await DAOPools.get_pool_action(pool_category=PoolCategory.NONE)
    if active_pool is None:
        return

    if active_pool.end_date <= datetime.now().date():
        await DAOPools.update_pool_actions(pool_id=active_pool.pool_uuid)


#     # 1) Закрыть просроченные опросы
#     async with db_helper.session_factory() as session:
#         await close_expired_polls(session, today)
#
#     # 2) Найти опрос, стартующий сегодня
#     async with db_helper.session_factory() as session:
#         poll = await get_poll_starting_today(session, today)
#
#     if poll is None:
#         logger.info("Нет опроса на сегодня — выходим")
#         return
#
#     # 3) Получатели
#     if test_users is not None:
#         recipients = test_users
#     else:
#         async with db_helper.session_factory() as session:
#             recipients = await get_all_user_ids(session)
#
#     logger.info("Рассылаем опрос %s → %d получателей", poll.id, len(recipients))
#
#     # 4) Рассылка
#     for user_id in recipients:
#         await send_message_text_to_user(
#             uuid=str(user_id),
#             text=poll.text,
#         )
#
#
# async def close_expired_polls(session, today: date) -> None:
#     """Закрывает опросы, у которых end_date < today и is_active=True."""
#     # пример на SQLAlchemy 2.0 — подгоните под свою модель
#     from sqlalchemy import update
#     from database.models import Poll  # ваш модуль
#
#     stmt = (
#         update(Poll)
#         .where(Poll.is_active == True, Poll.end_date < today)
#         .values(is_active=False)
#     )
#     result = await session.execute(stmt)
#     await session.commit()
#     logger.info("Закрыто просроченных опросов: %d", result.rowcount)
#
#
# async def get_poll_starting_today(session, today: date):
#     from sqlalchemy import select
#     from database.models import Poll
#
#     stmt = select(Poll).where(
#         Poll.is_active == True,
#         Poll.start_date == today,
#     ).limit(1)
#     return (await session.execute(stmt)).scalar_one_or_none()
#
#
# async def get_all_user_ids(session) -> list[int]:
#     from sqlalchemy import select
#     from database.models import User
#
#     stmt = select(User.id)  # или User.telegram_id — что у вас
#     return [row[0] for row in (await session.execute(stmt)).all()]

async def daily_pool_test_job(uuid: list[str] | None = None, text: str = "") -> None:
    """
    Ежедневная задача 09:00 по Минску.

    test_users=None  → боевой режим, рассылка всем пользователям
    test_users=[...] → тестовый режим, только этим ID
    """
    logger.info("🔔 daily_pool_job start")

    #     Получаем активный пул если существует
    active_pool = await DAOPools.get_pool_action(pool_category=PoolCategory.NONE)
    if active_pool is None:
        print("skjcdbaksdnckajsnckjasnckjsadncakjnckjcnkjanc")
        return

    if uuid is not None:
        print(f" Дата рула ---------- {active_pool.end_date.strftime("%d-%m-%Y")}")
        print(datetime.now().date())
        for user in uuid:
            await send_message_text_to_user(uuid=str(user), text=text)
    if active_pool.end_date < datetime.today().date():
        logger.info(f"Опрос {active_pool.id} закрываем")
        await DAOPools.update_pool_actions(id=active_pool.id)

    print(active_pool)


def register_jobs(scheduler: AsyncIOScheduler) -> None:
    """Регистрация всех периодических задач. Вызывать один раз при старте."""
    scheduler.add_job(
        daily_pool_job,
        trigger=CronTrigger(hour=9, minute=0),  # каждый день 09:00 Europe/Minsk
        id="daily_pool_job",
        replace_existing=True,
        misfire_grace_time=3600,  # если бот лежал — догонит в течение часа
        coalesce=True,  # не запускать 10 раз подряд после простоя
        max_instances=1,  # не пересекать запуски
    )

    logger.info("✅ daily_pool_job зарегистрирован (cron 09:00 Europe/Minsk)")

    scheduler.add_job(daily_pool_test_job,
                      "date",
                      run_date=datetime.now() + timedelta(minutes=1),
                      kwargs={
                          "uuid": settings.TEST_USERS,
                          "text": "Проверка выполнения задания по рассписани, сообщение только админам",
                      },
                      )
