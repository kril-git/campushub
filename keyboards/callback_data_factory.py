from aiogram.filters.callback_data import CallbackData


class PoolsCallbackFactory(CallbackData, prefix="pool"):
    pool_id: int
    pool_question: int
    pool_answer: int


class PoolContinueFactory(CallbackData, prefix="continue"):
    step: int
