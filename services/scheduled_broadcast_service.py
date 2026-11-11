import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from config import bot
from core.config import settings
from database.connection import connection, readonly
from database.dao.scheduled_broadcast_dao import ScheduledBroadcastDAO
from models import ScheduledBroadcast
from services.EnumBroadcastStatus import BroadcastStatus
from services.recipients_services import RecipientsService
from services.sending_service import broadcast_text_all_users, broadcast_photo_all_users, send_message_text_to_user

logger = logging.getLogger(__name__)


class ScheduledBroadcastService:

    @staticmethod
    @readonly
    async def get_pending(session: AsyncSession, now: datetime | None = None) -> list[ScheduledBroadcast]:
        """Возвращает pending-рассылки, которые пора отправить."""
        if now is None:
            now = datetime.now(ZoneInfo("Europe/Minsk"))
        return await ScheduledBroadcastDAO.get_pending(session=session, now=now)

    @staticmethod
    @connection
    async def schedule(
        session: AsyncSession,
        text: str | None,
        photo_file_id: str | None,
        scheduled_at: datetime,
        created_by: str,
    ) -> ScheduledBroadcast:
        """Создаёт запланированную рассылку."""
        bc = ScheduledBroadcast(
            text=text,
            photo_file_id=photo_file_id,
            scheduled_at=scheduled_at,
            status=BroadcastStatus.PENDING,
            created_by=created_by,
        )
        instance = await ScheduledBroadcastDAO.add(session=session, data=bc)
        logger.info(
            "scheduled broadcast created: id=%s, at=%s, created_by=%s",
            instance.id, scheduled_at, created_by,
        )
        return instance

    @staticmethod
    @connection
    async def cancel(session: AsyncSession, broadcast_id: int) -> bool:
        """Отменяет запланированную рассылку."""
        bc = await ScheduledBroadcastDAO.get_by_id(session=session, broadcast_id=broadcast_id)
        if bc is None or bc.status != BroadcastStatus.PENDING:
            return False
        await ScheduledBroadcastDAO.mark_cancelled(session=session, broadcast_id=broadcast_id)
        logger.info("scheduled broadcast cancelled: id=%s", broadcast_id)
        return True

    @staticmethod
    async def process_pending() -> dict:
        """
        Берёт все pending-рассылки, которые пора отправить, и отправляет.
        Возвращает {'sent': N, 'failed': M, 'skipped': 0}.
        """
        from datetime import datetime as dt
        now = dt.now(ZoneInfo("Europe/Minsk"))
        pending = await ScheduledBroadcastService.get_pending(now=now)

        if not pending:
            return {"sent": 0, "failed": 0, "skipped": 0}

        logger.info("process_pending: найдено %d", len(pending))

        recipients = await RecipientsService.get_recipients()
        if not recipients:
            logger.warning("process_pending: нет получателей")
            return {"sent": 0, "failed": 0, "skipped": len(pending)}

        sent = failed = 0
        for bc in pending:
            try:
                if bc.photo_file_id:
                    ok, failed_count, errors = await broadcast_photo_all_users(
                        bot=bot,
                        recipients=recipients,
                        photo=bc.photo_file_id,
                        text=bc.text or "",
                        save_last_message=True,
                    )
                else:
                    ok, failed_count, errors = await broadcast_text_all_users(
                        bot=bot,
                        recipients=recipients,
                        text=bc.text or "",
                        save_last_message=True,
                    )

                await ScheduledBroadcastService._mark_sent(bc.id)
                sent += 1
                logger.info(
                    "scheduled broadcast id=%s отправлен: ok=%d, failed=%d",
                    bc.id, ok, failed_count,
                )
                await send_message_text_to_user(
                    uuid=str(settings.MAIN_ADMIN),  # ← вот сюда
                    text=f"Запланированное сообщение отправлено id={bc.id}\n\n"
                         f"ok={ok}\nfailed={failed_count}",
                )

            except Exception as e:
                logger.exception("Ошибка scheduled broadcast id=%s: %s", bc.id, e)
                await ScheduledBroadcastService._mark_failed(bc.id, str(e))
                failed += 1

        return {"sent": sent, "failed": failed, "skipped": 0}

    @staticmethod
    @connection
    async def _mark_sent(session: AsyncSession, broadcast_id: int) -> None:
        await ScheduledBroadcastDAO.mark_sent(session=session, broadcast_id=broadcast_id)

    @staticmethod
    @connection
    async def _mark_failed(session: AsyncSession, broadcast_id: int, error: str) -> None:
        await ScheduledBroadcastDAO.mark_failed(
            session=session, broadcast_id=broadcast_id, error=error,
        )