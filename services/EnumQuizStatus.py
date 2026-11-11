from enum import Enum


class QuizStatus(str, Enum):
    """
    Статус квиза.

    - DRAFT: черновик (загружен, но не запущен)
    - ACTIVE: активен (можно проходить)
    - FINISHED: завершён (нельзя проходить)
    """
    DRAFT = "draft"
    ACTIVE = "active"
    FINISHED = "finished"

    @classmethod
    def from_value(cls, value: str | None) -> "QuizStatus":
        """Безопасный парсинг. Если None/мусор — DRAFT."""
        if not value:
            return cls.DRAFT
        try:
            return cls(value.lower())
        except ValueError:
            return cls.DRAFT

    @classmethod
    def values(cls) -> list[str]:
        """Все значения (для валидации)."""
        return [item.value for item in cls]

    def is_active(self) -> bool:
        return self == QuizStatus.ACTIVE

    def is_finished(self) -> bool:
        return self == QuizStatus.FINISHED

    def is_draft(self) -> bool:
        return self == QuizStatus.DRAFT