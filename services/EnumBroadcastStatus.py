from enum import Enum


class BroadcastStatus(str, Enum):
    """Статус запланированной рассылки."""
    PENDING = "pending"       # ждёт отправки
    SENT = "sent"             # успешно отправлена
    FAILED = "failed"         # ошибка при отправке
    CANCELLED = "cancelled"   # отменена вручную