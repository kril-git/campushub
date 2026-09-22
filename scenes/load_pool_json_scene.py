from datetime import datetime
from datetime import date

import logging

from aiogram import Router, F
from aiogram.enums import ContentType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import Scene, on
from aiogram.types import Message, ReplyKeyboardRemove

from core.config import settings
from keyboards.reply_keyboar import r_kb_load_exit, r_kb_exit
from services.pool_services import get_data_from_json, create_pool, get_info_pool

router = Router(name=__name__)
logger = logging.getLogger(__name__)


class LoadPoolJsonScene(Scene, state="load_pool_json_scene"):

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
        if message.document.mime_type != "application/json":
            await message.answer("Я ожидаю JSON файл.")
            return

        data = await get_data_from_json(message)
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
              or datetime.strptime(data.get("start_date"), "%d.%m.%Y").date() >= datetime.strptime(data.get("end_date"), "%d.%m.%Y").date()):
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


# router.message.register(
#     LoadPoolJsonScene.as_handler(),
#     Command("json_pool_load"),
# )