import logging

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import Scene, on
from aiogram.types import Message, CallbackQuery
from aiogram import F

from keyboards.inline_keyboard import  i_kb_yes_or_no
from keyboards.reply_keyboar import r_kb_accounting
from lexicon.lexicon_ru import  LEXICON_ADD_PRODUCTS, LEXICON_ADD_PRODUCTS_PROCESS_FULL
from services.accounting_service import get_str_add_product

router = Router(name=__name__)
logger = logging.getLogger(__name__)


class AccountingProductsScene(Scene, state="accounting_products_scene"):
    # keyboard = create_i_kb_from_dict(data=LEXICON_DIRECTORIES_SCENE, adjust=1)
    #
    # @on.message.enter()
    # async def on_enter(self, message: Message, state: FSMContext):
    #     # return
    #     await message.answer(text="Перешли в раздел учета.", reply_markup=ReplyKeyboardRemove())
    #     await message.answer(text="Зто ваши настройки. Выберите пункт ниже",
    #                          reply_markup=self.keyboard
    #                          )

    @on.callback_query(F.data == "exit")
    async def on_enter_cb(self, callback: CallbackQuery):
        await callback.message.answer(text="CallbackQuery")
        await self.wizard.exit()

    @on.callback_query(F.data == "products")
    async def on_products_cb(self, callback: CallbackQuery):
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(text="Перешли в раздел управления ассортиментом.", reply_markup=r_kb_accounting)

    @on.message(F.text.lower().contains("добавить".lower()))
    async def product_add(self, message: Message, state: FSMContext):
        """
        step - шаг обработки процесса добавления товар, если 0, то это начало процесса;
        count - количество шагов;
        state_product - текущий выбор процесса;
        """
        data = await state.get_data()
        if data.get("step") is None:
            await state.update_data(step=0)
            await state.update_data(state_product="add")
            await state.update_data(count=len(LEXICON_ADD_PRODUCTS_PROCESS_FULL))
            data = await state.get_data()
            await message.answer(text=LEXICON_ADD_PRODUCTS, reply_markup=i_kb_yes_or_no)

            logger.info(f"handler {message.text} - step {data.get("step")} -  count {data.get("count")} ")
        else:
            await message.answer(text=f"Вы уже находитесь в разделе Добавить товар,\n"
                                      f"Введите {LEXICON_ADD_PRODUCTS_PROCESS_FULL[data.get("step")]}")
            logger.info(f"handler {message.text} - step {data.get("step")} -  count {data.get("count")} ")

    @on.callback_query(F.data == "product_add_yes")
    async def get_new_product(self, callback: CallbackQuery, state: FSMContext):
        await callback.message.edit_reply_markup(reply_markup=None)
        data = await state.get_data()
        if data.get("step") == 0:
            await callback.message.answer(text=f"ПОЕХАЛИ - count - {data.get("count")}, step - {data.get("step")}")

            await state.update_data(step=data.get("step") + 1)
            data = await state.get_data()

            await callback.message.answer(text=get_str_add_product(step=data.get("step")))
        else:
            if data.get("step") < data.get("count"):
                await state.update_data(step=data.get("step") + 1)
                data = await state.get_data()
                logger.info(f"handler {callback.message.text} - step {data.get("step")} -  count {data.get("count")} ")

                await callback.message.answer(text=get_str_add_product(step=data.get("step")))

            else:
                await callback.message.answer(text="процесс завершен")

    @on.message(F.text)
    async def get_str(self, message: Message, state: FSMContext):
        data = await state.get_data()
        for k, v in data.items():
            print(k, v)
        await message.answer(text=f" {message.text}\n\nПодтвердите что все правильно", reply_markup=i_kb_yes_or_no)


    @on.message()
    # @Action(F.text)
    async def unknown_message(self, message: Message) -> None:
        await message.answer("Please select an answer.")

    @on.callback_query.exit()
    async def exit(self, callback: CallbackQuery, state: FSMContext):
        await callback.message.answer(text="вышли из сцены")
        await state.clear()
        await callback.message.edit_reply_markup(reply_markup=None)
        current_state = await state.get_state()
        await callback.message.answer(f"Текущее состояние: {current_state}")


# pip install -U aiogram
# python3 -m pip install -U aiogram
# router.message.register(AccountingScene.as_handler(), Command("accounting"))
