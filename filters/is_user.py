from aiogram.filters import BaseFilter
from aiogram.types import Message

from core.config import settings


class IsUser(BaseFilter):
    async def __call__(self, message: Message):
        if not str(message.from_user.id) in settings.ADMINS:
            return True
        else:
            return False
