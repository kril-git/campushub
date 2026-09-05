# import logging
#
# from aiogram import Router, F, flags
# from aiogram.enums import ChatAction, ContentType
# from aiogram.filters import Command
# from aiogram.fsm.context import FSMContext
# from aiogram.fsm.scene import Scene, on
# from aiogram.types import Message, ReplyKeyboardRemove
#
# from keyboards.reply_keyboar import r_kb_load_exit, r_kb_exit
# from services.pool_services import get_data_from_json, create_pool, get_info_pool
#
# router = Router(name=__name__)
# logger = logging.getLogger(__name__)
#
#
# class LoadPoolJsonScene(Scene, state="load_pool_json_scene"):
#
#     @on.message.enter()
#     @flags.chat_action(action=ChatAction.TYPING)
#     async def on_enter(self, message: Message, state: FSMContext):
#         print(await state.get_state())
#         await message.answer(text=f"Пожалуйста, загрузите файл в формате JSON.\n"
#                                   f"Если Вы готовы, нажмите кнопку 'Загрузить', иначе выберите 'Выход'\n"
#                                   f"👇",
#                              reply_markup=r_kb_load_exit)
#
#     @on.message(F.text.contains("Загрузить"))
#     @flags.chat_action(action=ChatAction.UPLOAD_DOCUMENT)
#     async def load_json_wait(self, message: Message, state: FSMContext):
#         await message.answer(text="Жду файл 🕰", reply_markup=r_kb_exit)
#
#     @on.message(F.content_type == ContentType.DOCUMENT)
#     @flags.chat_action(action=ChatAction.UPLOAD_DOCUMENT)
#     async def load_json(self, message: Message, state: FSMContext):
#         if message.document.mime_type == "application/json":
#             data = await get_data_from_json(message)
#             if data:
#                 id_pool = await create_pool(data=data, state=state)
#                 await message.answer(text=await get_info_pool(pool_id=id_pool), reply_markup=ReplyKeyboardRemove())
#                 await message.answer(text=f"Если что то не корректно, отредактируйте JSON-файл и повторите действия."
#                                           f" /json_pool_load")
#             else:
#                 await message.answer("Убедитесь в пароле и загрузите файл повторно.\n"
#                                      "Жду файл 🕰")
#                 logger.error("Пароль в файле не соответствует")
#         else:
#             await message.answer(f"Я ожидаю JSON файл.")
#
#     @on.message(F.text.contains("Выход"))
#     async def exit(self, message: Message, state: FSMContext) -> None:
#         await message.answer(text="Загрузка файла отменена.", reply_markup=ReplyKeyboardRemove())
#         await self.wizard.exit()
#
#     @on.message()
#     async def unknown_message(self, message: Message) -> None:
#         """
#         Method triggered when the user sends a message that is not a command or an answer.
#
#         It asks the user to select an answer.
#
#         :param message: The message received from the user.
#         :return: None
#         """
#         await message.answer("Please select an answer.")
#
#     # @on.message(Command(commands="json_pool_load"))
#     # async def load_file(self, message: Message):
#     #     await message.answer(text="CallbackQuery")
#     #     await self.wizard.exit()
#
#
# router.message.register(LoadPoolJsonScene.as_handler(), Command("json_pool_load"))
