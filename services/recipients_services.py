import logging

from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import readonly
from database.dao.recipients_dao import RecipientsDAO

logger = logging.getLogger(__name__)


class RecipientsService:
    @staticmethod
    @readonly
    async def get_all_telegram_ids(session: AsyncSession) -> list[str]:
        """
                Возвращает список telegram_id всех зарегистрированных пользователей.
                Фильтрует пустые значения (страховка).
        """

        raw = await RecipientsDAO.get_real_recipients(session=session)
        recipients = [str(u) for u in raw if u and str(u).strip()]
        logger.info("RecipientsService.get_all_telegram_ids: %d валидных из %d", len(recipients), len(raw))
        return recipients

    @staticmethod
    @readonly
    async def get_not_completed_telegram_ids(
            session: AsyncSession, pool_id: int
    ) -> list[str]:
        """Все telegram_id, кто НЕ прошёл опрос pool_id."""
        raw = await RecipientsDAO.get_recipients_excluding_completed(
            session=session, pool_id=pool_id,
        )
        recipients = [str(u) for u in raw if u and str(u).strip()]
        logger.info(
            "get_not_completed_telegram_ids(pool_id=%s): %d из %d",
            pool_id, len(recipients), len(raw),
        )
        return recipients

    @staticmethod
    async def get_recipients_all(
            override: list[str] | None = None,
    ) -> list[str]:
        """
        Оркестратор: получатели по режиму.
        - override=[...] — явный список (ручной запуск);
        - TEST_MODE=True → TEST_USERS;
        - TEST_MODE=False → реальные из БД;
        - force_real=True — игнорировать TEST_MODE.
        """
        if override is not None:
            logger.info("get_recipients: override (%d)", len(override))
            return override

        real = await RecipientsService.get_all_telegram_ids()
        logger.info("get_recipients: TEST_MODE=False → real (%d)", len(real))
        return real

    @staticmethod
    async def get_recipients(
            override: list[str] | None = None,
            pool_id: int | None = None,
            skip_filter: bool = False
    ) -> list[str]:
        """
        - override=[...] → явный список;
          - если pool_id и не skip_filter → отфильтровать прошедших;
        - pool_id → только те, кто НЕ прошёл pool_id;
        - pool_id=None → все реальные из БД.
        """
        if override is not None:
            if pool_id is not None and not skip_filter:
                not_completed = await RecipientsService.get_not_completed_telegram_ids(pool_id=pool_id)
                not_completed_set = {str(u) for u in not_completed}
                filtered = [str(u) for u in override if str(u) in not_completed_set]
                logger.info(
                    "get_recipients: override (%d) → filtered by pool=%s (%d)",
                    len(override), pool_id, len(filtered),
                )
                return filtered

            logger.info("get_recipients: override (%d), skip_filter=%s", len(override), skip_filter)
            return [str(u) for u in override]

        if pool_id is not None:
            real = await RecipientsService.get_not_completed_telegram_ids(pool_id=pool_id)
            logger.info("get_recipients: not_completed pool=%s (%d)", pool_id, len(real))
            return real

        real = await RecipientsService.get_all_telegram_ids()
        logger.info("get_recipients: real (%d)", len(real))
        return real