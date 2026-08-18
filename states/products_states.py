from aiogram.fsm.state import StatesGroup, State


class FSMProducts(StatesGroup):
    products = State()
    view = State()
    find = State()
    add = State()
    add_ok_no_ok = State()
    add_no_ok = State()
    delete = State()
    cancel = State()
    exit = State()
