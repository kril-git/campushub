# services/scheduled_jobs.py
import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import settings, bot
# from core.dependencies import AppDependencies
from database.dao.pool_dao import DAOPools, PoolDAO
from keyboards.inline_keyboard import create_i_kb_from_dict
from services.EnumPools import PoolCategory
from services.pool_service import PoolService
from services.sending_service import send_message_text_to_user, broadcast_text_all_users

logger = logging.getLogger(__name__)


# async def daily_pool_job(test_users: list[int] | None = None) -> None:
#     """
#     Ежедневная задача 09:00 по Минску.
#
#     test_users=None  → боевой режим, рассылка всем пользователям
#     test_users=[...] → тестовый режим, только этим ID
#     """
#     # tz = AppDependencies.tz
#     # today = datetime.now(tz).date()
#     logger.info("🔔 daily_pool_job start")
#
#     #     Получаем активный пул если существует
#     # active_pool = await DAOPools.get_pool_action(pool_category=PoolCategory.NONE)
#     active_pool = await PoolDAO.get_id_action(pool_category=PoolCategory.NONE)
#     if active_pool is None:
#         logger.info("Нет опроса на сегодня — выходим")
#         return
#


    # if active_pool.end_date <= datetime.now().date():
    #     await DAOPools.update_pool_actions(pool_id=active_pool.pool_uuid)


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

async def daily_send_pool_job(uuid: list[str] | None = None, text: str = "") -> None:
    """
    Ежедневная задача 09:00 по Минску.

    test_users=None  → боевой режим, рассылка всем пользователям
    test_users=[...] → тестовый режим, только этим ID
    """
    logger.info("🔔 daily_pool_job start")

    #     Получаем активный пул если существует
    active_pool_id = await PoolService.get_active_pool_id(pool_category=PoolCategory.NONE)
    # active_pool_id = await PoolService.get_active_pool_end_date(pool_category=PoolCategory.NONE)
    if active_pool_id is None:
        await send_message_text_to_user(uuid=str(uuid), text=f"Сегодня активного опроса нет.")
        return
    else:
        # await broadcast_text_all_users()
        data = {}
        data.update({"complete_a_survey": "Пройти опрос"})
        data.update({"exit_complete_a_survey": "Потом"})
        kbd = create_i_kb_from_dict(data=data, adjust=1)
        ok, failed = await broadcast_text_all_users(bot=bot,
                                                    recipients=settings.TEST_USERS,
                                                    text=text,
                                                    reply_markup=kbd,
                                                    )
        await send_message_text_to_user(uuid=settings.MAIN_ADMIN,
                                        text=f"Отправлен опрос\n"
                                             f"ok - {ok}\n"
                                             f"failed - {failed}")

async def mark_as_deleted_pool_job() -> None:
    """
        Ежедневная задача 0:01 по Минску.

        Проверяет активный опрос и помечает его как оконченный если дата окончания опроса вчера

    """
    logger.info("🔔 mark_as_deleted_pool_job start")
    active_pool_id = await PoolService.get_active_pool_end_date_yesterday(pool_category=PoolCategory.NONE)
    if active_pool_id is None:
        await send_message_text_to_user(uuid=settings.MAIN_ADMIN, text=f"Пула для удаления нет")
        return
    else:
        await send_message_text_to_user(uuid=settings.MAIN_ADMIN, text=f"пул для удаления ID =  {active_pool_id}")
        if await PoolService.mark_as_deleted_pool(pool_id=active_pool_id):
            await send_message_text_to_user(uuid=settings.MAIN_ADMIN,
                                            text=f"пул ID =  {active_pool_id}, успешно помечен как не активный"
                                            )


def register_jobs(scheduler: AsyncIOScheduler) -> None:
    """Регистрация всех периодических задач. Вызывать один раз при старте."""
    scheduler.add_job(
        mark_as_deleted_pool_job,
        trigger=CronTrigger(hour=0, minute=1),  # каждый день 0:01 Europe/Minsk
        id="mark_as_deleted_pool_job",
        replace_existing=True,
        misfire_grace_time=3600,  # если бот лежал — догонит в течение часа
        coalesce=True,  # не запускать 10 раз подряд после простоя
        max_instances=1,  # не пересекать запуски
    )

    logger.info("✅ mark_as_deleted_pool_job зарегистрирован (cron 0:01 Europe/Minsk)")

    scheduler.add_job(daily_send_pool_job,
                      "date",
                      run_date=datetime.now() + timedelta(minutes=1),
                      kwargs={
                          "uuid": settings.TEST_USERS,
                          "text": f"Вам необходимо пройти опрос",
                      },
                      )


    # scheduler.add_job(daily_pool_test_job,
    #                   "date",
    #                   run_date=datetime.now() + timedelta(minutes=1),
    #                   kwargs={
    #                       "uuid": settings.TEST_USERS,
    #                       "text": "Проверка выполнения задания по рассписани, сообщение только админам",
    #                   },
    #                   )