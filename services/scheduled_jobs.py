# services/scheduled_jobs.py
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.fsm import storage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import settings, bot
# from core.dependencies import AppDependencies
from database.dao.pool_dao import DAOPools, PoolDAO
from keyboards.inline_keyboard import create_i_kb_from_dict, generate_inline_keyboard_for_question
from services.EnumPools import PoolCategory
from services.pool_service import PoolService
from services.recipients_services import RecipientsService
from services.report_service import ReportService
from services.sending_service import send_message_text_to_user, broadcast_text_all_users, LAST_BROADCAST_MSG_ID
from services.services import _to_chat_id
from utils.cleanup_old_survey_messages import cleanup_old_survey_messages

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

    # 1️⃣ СРАЗУ ОПРЕДЕЛЯЕМ ПОЛУЧАТЕЛЕЙ (чтобы знать, у кого чистить экран)
    recipients = uuid if uuid is not None else settings.TEST_USERS
    await cleanup_old_survey_messages(bot=bot, recipients=recipients)
    # 2️⃣ ЭТАП ЗАЧИСТКИ (ВЫПОЛНЯЕТСЯ ВСЕГДА): Удаляем вчерашние висящие опросы с экрана [💡]
    for raw_id in recipients:
        chat_id = _to_chat_id(raw_id)
        if chat_id is None:
            continue

        try:
            from core.dependencies import AppDependencies

            storage_key = StorageKey(bot_id=bot.id, chat_id=chat_id, user_id=chat_id, destiny="default")
            user_state = FSMContext(storage=AppDependencies.storage, key=storage_key)

            user_fsm_data = await user_state.get_data()
            old_message_id = user_fsm_data.get(LAST_BROADCAST_MSG_ID)

            # if old_message_id:
            #     # Стираем вчерашнее сообщение, чат теперь идеально чистый [💡]
            #     await bot.delete_message(chat_id=chat_id, message_id=old_message_id)
            #
            #     # Не забываем стереть этот ID из Redis, так как сообщения больше нет в природе
            #     await user_state.update_data({LAST_BROADCAST_MSG_ID: None})
        except Exception:
            pass

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
                                                    save_last_message=True,
                                                    )
        await send_message_text_to_user(uuid=settings.MAIN_ADMIN,
                                        text=f"Отправлен опрос\n"
                                             f"ok - {ok}\n"
                                             f"failed - {failed}\n"
                                             f"pool - {active_pool_id}\n")


async def direct_send_pool_job(recipients: list[int] | None = None, text: str = "") -> None:
    """
    Рассылка первого вопроса активного пула 'прямо в лоб'.

    - Если recipients=None — берём settings.TEST_USERS.
    - Перед рассылкой — чистим вчерашние висящие сообщения.
    - Кнопки — start_pool_click (сразу в сцену, без промежуточного 'Пройти / Потом').
    """
    logger.info("🔔 Запуск direct_send_pool_job")

    # 1. Активный пул
    active_pool_id = await PoolService.get_active_pool_id()
    if active_pool_id is None:
        logger.info("Нет активных опросов на сегодня. Джоб direct_send_pool_job завершен.")
        return

    # 2. Получатели
    # target_users = recipients if recipients is not None else settings.TEST_USERS
    target_users = await RecipientsService.get_recipients(override=recipients,
                                                          pool_id=active_pool_id)

    target_strs = [str(u) for u in target_users]
    logger.warning(
        "🔍 получателей=%d, есть ли 7740157654? %s",
        len(target_users), "7740157654" in target_strs,
    )

    if not target_users:
        logger.warning("direct_send_pool_job: нет получателей")
        return

    # 3. Чистка вчерашних сообщений для всех зарегистрированных пользователей
    all_users = await RecipientsService.get_all_telegram_ids()

    await cleanup_old_survey_messages(recipients=[str(u) for u in all_users])

    # 4. Первый вопрос
    first_q = await PoolService.get_first_question_of_pool(pool_id=active_pool_id)
    if not first_q:
        logger.warning("Пул %s активен, но в нем нет вопросов!", active_pool_id)
        return

    # 5. Клавиатура — одна на всех (не в цикле!)
    kbd = generate_inline_keyboard_for_question(
        buttons=first_q.poolanswer,
        prefix=f"start_pool_click:{active_pool_id}:{first_q.question_number}",
    )

    # 6. Рассылка — broadcast сам обходит получателей (без внешнего for!)
    ok, failed = await broadcast_text_all_users(
        bot=bot,
        recipients=[str(u) for u in target_users],
        text=f"<b>📊 Доступен новый опрос!</b>\n\n{first_q.pool_question}",
        reply_markup=kbd,
        save_last_message=True,   # ← сохранит message_id для завтрашней чистки
    )
    logger.info("direct_send_pool_job: ok=%s, failed=%s", ok, failed)

    # 7. Уведомление админа (опционально)
    await send_message_text_to_user(
        uuid=str(settings.MAIN_ADMIN),
        text=(
            f"📤 direct_send_pool_job завершён\n"
            f"pool={active_pool_id}\n"
            f"ok={ok}\nfailed={failed}"
        ),
    )


async def mark_as_deleted_pool_job() -> None:
    """
    Ежедневная задача 0:01 по Минску.
    Помечает опрос как оконченный, если дата окончания вчера.
    После закрытия — генерирует Excel-отчёт и отправляет админу.
    """
    logger.info("🔔 mark_as_deleted_pool_job start")

    active_pool_id = await PoolService.get_active_pool_end_date_yesterday(
        pool_category=PoolCategory.NONE
    )
    if active_pool_id is None:
        await send_message_text_to_user(
            uuid=settings.MAIN_ADMIN,
            text="Пула для удаления нет",
        )
        return

    await send_message_text_to_user(
        uuid=settings.MAIN_ADMIN,
        text=f"Пул для удаления ID = {active_pool_id}",
    )

    # 1. Помечаем как неактивный
    if not await PoolService.mark_as_deleted_pool(pool_id=active_pool_id):
        await send_message_text_to_user(
            uuid=settings.MAIN_ADMIN,
            text=f"❌ Пул {active_pool_id} не удалось пометить как неактивный",
        )
        return

    await send_message_text_to_user(
        uuid=settings.MAIN_ADMIN,
        text=f"✅ Пул {active_pool_id} успешно помечен как неактивный. Генерирую отчёт...",
    )

    # 2. Генерируем и отправляем отчёт
    try:
        await ReportService.send_pool_report_to_admin(pool_id=active_pool_id)
        logger.info("mark_as_deleted_pool_job: отчёт по пулу %s отправлен", active_pool_id)
    except Exception as e:
        logger.exception("Ошибка отправки отчёта pool=%s: %s", active_pool_id, e)
        await send_message_text_to_user(
            uuid=settings.MAIN_ADMIN,
            text=f"❌ Ошибка генерации отчёта по пулу {active_pool_id}: {e}",
        )
def register_jobs(scheduler: AsyncIOScheduler) -> None:
    now_in_minsk = datetime.now(ZoneInfo("Europe/Minsk"))
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

    # scheduler.add_job(daily_send_pool_job,
    #                   "date",
    #                   run_date=now_in_minsk + timedelta(minutes=2),
    #                   kwargs={
    #                       "uuid": settings.TEST_USERS,
    #                       "text": f"Вам необходимо пройти опрос",
    #                   },
    #                   )

    scheduler.add_job(daily_send_pool_job,
                      trigger=CronTrigger(hour=9, minute=30, timezone=ZoneInfo("Europe/Minsk")),
                      # каждый день 9:00 Europe/Minsk
                      id="daily_send_pool_job",
                      kwargs={
                          "uuid": settings.TEST_USERS,
                          "text": f"Вам необходимо пройти опрос",
                      },
                      replace_existing=True,
                      misfire_grace_time=3600,  # если бот лежал — догонит в течение часа
                      coalesce=True,  # не запускать 10 раз подряд после простоя
                      max_instances=1, )  # не пересекать запуски

    scheduler.add_job(direct_send_pool_job,
                      "date",
                      run_date=datetime.now() + timedelta(minutes=1),
                      kwargs={
                          "recipients": settings.TEST_USERS,
                          "text": "Проверка выполнения задания по рассписани, сообщение только админам",
                      },
                      )
