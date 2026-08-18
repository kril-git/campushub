from aiogram.filters import BaseFilter
from aiogram.types import Message

from core.config import settings


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message):
        if str(message.from_user.id) in settings.ADMINS:
            return True
        else:
            return False
