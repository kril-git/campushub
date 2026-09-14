from enum import Enum
from typing import Any


class PoolCategory(Enum):
    NONE = 0
    ALL = 1
    SALON = 2
    RETAIL = 3

    @classmethod
    def get_category(cls, value: str) -> str | Any:
        value = value.upper()
        for item in cls:
            if item.name == value:
                return item.name
        return cls.NONE
