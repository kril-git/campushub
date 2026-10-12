from datetime import datetime

import logging

logger = logging.getLogger(__name__)


class PersonalRecordValidator:
    REQUIRED_FIELDS = ("surname", "given_name", "phone", "birth_date")
    DATE_FORMAT = "%d.%m.%Y"

    @classmethod
    def validate_and_prepare(cls, user_data: dict, uuid: str) -> dict:
        """
        Проверяет данные, парсит дату, добавляет uuid.
        Возвращает НОВЫЙ dict (не мутирует входной).
        Бросает ValueError с человекочитаемым текстом.
        """
        cls._check_required(user_data)
        birth_date = cls._parse_date(user_data["birth_date"])

        return {
            **user_data,  # копия всех полей
            "uuid": uuid,  # добавляем uuid
            "birth_date": birth_date,  # заменяем строку на date
        }

    @classmethod
    def _check_required(cls, user_data: dict) -> None:
        missing = [f for f in cls.REQUIRED_FIELDS if f not in user_data or not user_data[f]]
        if missing:
            raise ValueError(f"Не заполнены поля: {', '.join(missing)}")

    @classmethod
    def _parse_date(cls, value: str):
        try:
            return datetime.strptime(value, cls.DATE_FORMAT).date()
        except (ValueError, TypeError):
            raise ValueError(
                f"Неверный формат даты: {value!r}. Ожидается дд.мм.гггг."
            )
