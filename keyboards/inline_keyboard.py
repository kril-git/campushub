from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.callback_data_factory import PoolsCallbackFactory, PoolContinueFactory
from models import PoolAnswer


#
# from keyboards.callback_data_factory import PoolsCallbackFactory, PoolContinueFactory
# from models import PoolAnswer
#
# i_kb_yes_or_no = InlineKeyboardMarkup(
#     inline_keyboard=[[InlineKeyboardButton(text='ДА', callback_data="product_add_yes"),
#                       InlineKeyboardButton(text='НЕТ', callback_data="product_add_no")]],
#     resize_keyboard=True, one_time_keyboard=True,
#     input_field_placeholder='Выберите пункт меню ...',
# )
#
# рабочий
def create_i_kb_from_dict(data: dict[str, str], adjust: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for callback, text in data.items():
        builder.add(InlineKeyboardButton(text=text, callback_data=callback))
    builder.adjust(adjust)
    return builder.as_markup()


def get_continue_cancel_keyboard_builder() -> InlineKeyboardMarkup:
    """Клавиатура с кнопками через Builder"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Продолжить", callback_data="continue")
    builder.button(text="❌ Отмена", callback_data="cancel")
    builder.adjust(2)  # 2 кнопки в ряд
    return builder.as_markup()


def i_kb_begin_or_exit(adjust: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="👌 Начать", callback_data="begin")
    builder.button(text="🚫 Выход", callback_data="exit")
    builder.adjust(adjust)  # 2 кнопки в ряд
    return builder.as_markup()


def create_i_kb_begin(pool_id: int, pool_question: int, pool_answer: int):
    builder = InlineKeyboardBuilder()
    builder.add((InlineKeyboardButton(text="Поехали",
                                      callback_data=PoolsCallbackFactory(
                                          pool_id=pool_id, pool_question=pool_question, pool_answer=pool_answer).pack()
                                      )))
    return builder.as_markup()


#
#
def create_i_kb_pool_answers(pool_id: int, pool_question: int, pool_answers: list[PoolAnswer]):
    builder = InlineKeyboardBuilder()
    for answer in pool_answers:
        builder.add(InlineKeyboardButton(text=answer.pool_answer,
                                         callback_data=PoolsCallbackFactory(
                                             pool_id=pool_id, pool_question=pool_question, pool_answer=answer.id).pack()
                                         )
                    )
    builder.adjust(1)
    return builder.as_markup()


#
#
def i_kb_continue(step: int):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Продолжить",
                                     callback_data=PoolContinueFactory(step=step).pack()
                                     )
                )
    return builder.as_markup()


def i_get_start_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для первого шага: Да / Нет"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, хочу", callback_data="start_reg"),
                InlineKeyboardButton(text="❌ Нет, не хочу", callback_data="cancel_reg")
            ]
        ]
    )


def i_get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопками Отмена и Назад (inline)"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="back"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_mid")
            ]
        ]
    )


def i_get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения данных"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, все верно", callback_data="confirm_yes"),
                InlineKeyboardButton(text="❌ Нет, исправить", callback_data="confirm_no")
            ],
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="back"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_mid")
            ]
        ]
    )


def generate_inline_keyboard_for_question(
        buttons: list[PoolAnswer],
        prefix: str
) -> InlineKeyboardMarkup:
    """
    Динамически генерирует инлайн-клавиатуру для вопроса.

    :param buttons: Список объектов PoolAnswer из связи question.poolanswer
    :param prefix: Строка префикса, например "survey_ans:23:2" или "start_pool_click:23:1"
    :return: Объект InlineKeyboardMarkup для отправки в bot.send_message
    """
    builder = InlineKeyboardBuilder()

    for answer in buttons:
        # answer.pool_answer — текст, который увидит пользователь на кнопке
        # answer.id — уникальный ID ответа в базе данных, крепим его к префиксу [💡]
        callback_data = f"{prefix}:{answer.id}"

        builder.add(
            InlineKeyboardButton(
                text=answer.pool_answer,  # Текст кнопки (например: "Да", "Нет")
                callback_data=callback_data
            )
        )

    # .adjust(1) располагает каждую кнопку на новой строке (одна под другой).
    # Если хотите кнопки в ряд (если они короткие), можно сделать .adjust(2) [💡]
    builder.adjust(1)

    return builder.as_markup()
