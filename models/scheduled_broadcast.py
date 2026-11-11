# models/scheduled_broadcast.py
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base
from models.mixin import Mixin
from services.EnumBroadcastStatus import BroadcastStatus


class ScheduledBroadcast(Base, Mixin):
    """Запланированная рассылка (текст + опционально фото)."""

    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_file_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True,
    )
    status: Mapped[BroadcastStatus] = mapped_column(
        Enum(BroadcastStatus),
        default=BroadcastStatus.PENDING,
        nullable=False,
        index=True,
    )
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)