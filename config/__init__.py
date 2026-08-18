__all__ = ("bot", "settings" )
import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from core.config import  settings

from core.config import settings

logger = logging.getLogger(__name__)

bot = Bot(token=settings.BOT_TOKEN,
          default=DefaultBotProperties(
                  parse_mode=ParseMode.HTML,
          ))
