from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message


class IsNotNoneStates(BaseFilter):
    async def __call__(self, message: Message, state: FSMContext) -> bool:
        if await state.get_state() is not None:
            return True
        else:
            return False
