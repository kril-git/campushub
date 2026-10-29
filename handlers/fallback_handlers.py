import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery

logger = logging.getLogger(__name__)
router = Router(name="fallback")


# ===== Старые (переходный период) =====

@router.callback_query(F.data.startswith("survey_ans:"))
async def survey_ans_fallback(callback: CallbackQuery):
    logger.warning(
        "🚨 FALLBACK survey_ans: data=%s, user=%s",
        callback.data, callback.from_user.id,
    )
    await callback.answer("Сессия истекла. Начните опрос заново.", show_alert=True)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass


@router.callback_query(F.data.startswith("start_pool_click:"))
async def start_pool_click_fallback(callback: CallbackQuery):
    logger.warning(
        "🚨 FALLBACK start_pool_click: data=%s, user=%s",
        callback.data, callback.from_user.id,
    )
    await callback.answer("Опрос больше неактивен.", show_alert=True)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass


# ===== Новые (единый префикс) =====

@router.callback_query(F.data.startswith("scene:"))
async def scene_fallback(callback: CallbackQuery):
    logger.warning(
        "🚨 FALLBACK scene: data=%s, user=%s",
        callback.data, callback.from_user.id,
    )
    await callback.answer("Сессия истекла. Начните заново.", show_alert=True)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass