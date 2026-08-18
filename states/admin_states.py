from aiogram.fsm.state import StatesGroup, State


class FSMSetUserToAdmin(StatesGroup):
    fill_uuid = State()
    cancel = State()


class FSMUserAnswers(StatesGroup):
    get_id = State()
    cansel = State()
