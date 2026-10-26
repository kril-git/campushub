import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import ScenesManager
from aiogram.types import CallbackQuery

from models import Answer, UserPool
from services.pool_service import PoolService

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("start_pool_click:"))
async def start_survey_in_front(callback: CallbackQuery, state: FSMContext, scenes: ScenesManager):
    logger.warning("🚨 ХЭНДЛЕР ВЫЗВАН: %s", callback.data)
    try:
        await callback.answer()
        logger.warning("✅ callback.answer() OK")

        _, pool_id, q_num, ans_id = callback.data.split(":")
        pool_id, q_num, ans_id = int(pool_id), int(q_num), int(ans_id)
        user_uuid_str = str(callback.from_user.id)
        logger.warning("✅ parsed: pool_id=%s, q_num=%s, ans_id=%s", pool_id, q_num, ans_id)

        try:
            await callback.message.delete()
            logger.warning("✅ message.delete() OK")
        except Exception as e:
            logger.warning("⚠️ message.delete() failed: %s", e)

        # ⚠️ КОД ДОЛЖЕН БЫТЬ ЗДЕСЬ, НЕ ВНУТРИ except!

        already = await PoolService.check_survey_completion(
            user_uuid=user_uuid_str, pool_id=pool_id,
        )
        logger.warning("✅ check_survey_completion=%s", already)

        if already:
            await callback.message.answer("Вы уже проходили этот опрос.")
            return

        current_question = await PoolService.get_object_pool_question_by_pool_id_and_number_q(
            pool_id=pool_id, number_q=q_num,
        )
        logger.warning("✅ current_question=%s", current_question)

        if current_question is None:
            await callback.message.answer("Вопрос не найден.")
            return

        first_answer = {
            "user_uuid": user_uuid_str,
            "pool_id": pool_id,
            "question_id": current_question.id,
            "answer_id": ans_id,
            "step": 0,
        }

        next_question = await PoolService.get_next_question(
            pool_id=pool_id, current_question_number=q_num,
        )
        logger.warning("✅ next_question=%s", next_question)

        if next_question:
            await state.update_data(user_data={
                "pool_id": pool_id,
                "step": 1,
                "current_question_id": next_question.id,
                "answers_list": [first_answer],
            })
            logger.warning("✅ state updated: %s", await state.get_data())

            logger.warning("📦 BEFORE scenes.enter")
            await scenes.enter("direct_survey_scene")
            logger.warning("📦 AFTER scenes.enter — УСПЕХ")
        else:
            await callback.message.answer("⏳ Сохраняю ваш ответ...")
            await PoolService.finish_survey(
                answers=[Answer(**first_answer)],
                user_pool=UserPool(
                    user_uuid=user_uuid_str, pool_id=pool_id,
                    end_pool=True, step=0,
                ),
            )
            await callback.message.answer("🎉 Спасибо! Вы успешно прошли опрос.")
            logger.warning("✅ Один вопрос — сохранено")

    except Exception as e:
        logger.error("💥 ИСКЛЮЧЕНИЕ В ХЭНДЛЕРЕ: %s", e, exc_info=True)
        # Пробуем сообщить пользователю
        try:
            await callback.message.answer(f"Ошибка: {e}")
        except Exception:
            pass