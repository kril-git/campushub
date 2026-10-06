import json
from datetime import datetime
from datetime import date

import logging
from json import JSONDecodeError

from aiogram import Router, F
from aiogram.enums import ContentType
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import Scene, on
from aiogram.types import Message, ReplyKeyboardRemove

from core.config import settings
from exceptions.jsonloaderror import JsonLoadError
from filters.is_admin import IsAdmin, is_admin
from keyboards.reply_keyboar import r_kb_load_exit, r_kb_exit
from services.pool_services import create_pool, get_info_pool

router = Router(name=__name__)
logger = logging.getLogger(__name__)


class LoadPoolJsonScene(Scene, state="load_pool_json_scene"):
    @staticmethod
    async def _get_data_from_json(message: Message) -> dict | None:
        """
            Скачивает документ из сообщения и парсит его как JSON.
            Вызывается только для админа — проверка до вызова.

            Возвращает dict или None (если что-то не так — уже ответил пользователю).
        """
        # ---------- 1. Проверка расширения ----------
        if not (message.document.file_name or "").lower().endswith(".json"):
            await message.answer("Нужен файл с расширением .json.")
            return None

        await message.answer(
            "Отлично, я получил нужный документ.\n"
            "<i>Проверяю его корректность.</i>"
        )

        # ---------- 2. Получаем файл ----------
        try:
            file_info = await message.bot.get_file(message.document.file_id)
        except TelegramAPIError as e:
            logger.error("get_file failed: %s", e)
            await message.answer("Не удалось получить файл из Telegram. Попробуйте снова.  /json_pool_load")
            return None

        try:
            downloaded_file = await message.bot.download_file(file_info.file_path)
        except TelegramAPIError as e:
            logger.error("download_file failed: %s", e)
            await message.answer("Не удалось скачать файл. Попробуйте снова.  /json_pool_load")
            return None

        # downloaded_file = await download_json_from_message(message=message)

        # ---------- 3. Парсим ----------
        try:
            downloaded_file.seek(0)
            raw = downloaded_file.read()
            text = raw.decode("utf-8-sig")
            data = json.loads(text)
        except JSONDecodeError as e:
            logger.error("JSONDecodeError: msg=%r line=%s col=%s", e.msg, e.lineno, e.colno)
            await message.answer(
                f"Файл не является корректным JSON.\n"
                f"Ошибка: <code>{e.msg}</code> (строка {e.lineno}, позиция {e.colno})."
            )
            return None
        except UnicodeDecodeError as e:
            logger.error("UnicodeDecodeError: %s", e)
            await message.answer(
                "Проблема кодировки. Сохраните файл в UTF-8 и попробуйте снова."
            )
            return None
        return data

    @on.message.enter()
    async def on_enter(self, message: Message, state: FSMContext) -> None:
        logger.debug("Enter LoadPoolJsonScene, state=%s", await state.get_state())
        await message.answer(
            text=(
                "Пожалуйста, загрузите файл в формате JSON.\n"
                "Если Вы готовы, нажмите кнопку 'Загрузить', иначе выберите 'Выход'\n"
                "👇"
            ),
            reply_markup=r_kb_load_exit,
        )

    @on.message(F.text == "👌 Загрузить")
    async def load_json_wait(self, message: Message, state: FSMContext) -> None:
        await message.answer(text="Жду файл 🕰", reply_markup=r_kb_exit)

    @on.message(F.content_type == ContentType.DOCUMENT)
    async def load_json(self, message: Message, state: FSMContext) -> None:
        if not is_admin(message.from_user.id):
            await message.answer("Нет доступа.")
            logger.warning("Non-admin tried to import JSON: user_id=%s username=%s",
                           message.from_user.id, message.from_user.username,
                           )
            return
        if message.document.mime_type != "application/json":
            await message.answer("Я ожидаю JSON файл.")
            return
        # try:
        data = await self._get_data_from_json(message=message)
        # except JsonLoadError as e:
        #     await message.answer(e.user_message)
        #     return
        if not data:
            await message.answer(
                # "Убедитесь в пароле и загрузите файл повторно.\n"
                "Жду корректный файл в JSON формате 🕰"
            )
            logger.error("JSON битый")
            return
        elif data.get("password") not in settings.PASSWORDS:
            await message.answer("Убедитесь в пароле и загрузите файл повторно.\n"
                                 "Жду файл 🕰")
            logger.error("Пароль в файле не соответствует")
            return

        elif datetime.strptime(data.get("start_date"), "%d.%m.%Y").date() < date.today():
            await message.answer(text=f"Дата начала опроса меньше текущей, проверьте дату")
            return
        elif (datetime.strptime(data.get("end_date"), "%d.%m.%Y").date() <= date.today()
              or datetime.strptime(data.get("start_date"), "%d.%m.%Y").date() >= datetime.strptime(data.get("end_date"),
                                                                                                   "%d.%m.%Y").date()):
            await message.answer(text="Проверьте дату окончания опроса она не корректна.")
            return
        else:
            await message.answer(text=f"Проверка файла прошла успешно 👍.\n"
                                      f"Название файла {message.document.file_name},"
                                      f"Записываю данные в базу данных...")
            id_pool = await create_pool(data=data, state=state)
            await state.update_data(pool_id=id_pool)

            await message.answer(
                text=await get_info_pool(pool_id=id_pool),
                reply_markup=ReplyKeyboardRemove(),
            )
            await message.answer(
                text="Если что-то не корректно, отредактируйте JSON-файл "
                     "и повторите: /create_pool"
            )

    @on.message(F.text == "🚫 Выход")
    async def exit(self, message: Message, state: FSMContext) -> None:
        await message.answer(
            text="Загрузка файла отменена.",
            reply_markup=ReplyKeyboardRemove(),
        )
        await self.wizard.exit()

    @on.message(Command("cancel"))
    async def cancel(self, message: Message, state: FSMContext) -> None:
        await message.answer(
            text="Загрузка файла отменена.",
            reply_markup=ReplyKeyboardRemove(),
        )
        await self.wizard.exit()

    @on.message()
    async def unknown_message(self, message: Message) -> None:
        await message.answer(
            "Пожалуйста, выберите действие: 'Загрузить' или 'Выход'."
        )


