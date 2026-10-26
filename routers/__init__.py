__all__ = ("router", "get_scenes")  # Исправили кортеж в __all__

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.scene import Scene

from handlers.base_handlers import router as echo_router
from handlers.admin_handlers import router as admin_router
from handlers.test_handlers import router as test_router
from handlers.cancel_handler import router as cancel_router
from handlers.survey_starter import router as survey_starter_router

from scenes import registration_scene
from scenes.registration_scene import RegistrationScene

from scenes import broadcast_text_scene
from scenes.broadcast_text_scene import BroadcastScene

from scenes import load_pool_json_scene
from scenes.load_pool_json_scene import LoadPoolJsonScene

from scenes import complete_a_survey_scene
from scenes.complete_a_survey_scene import CompleteSurvey

from scenes import direct_survey_scene
# from scenes.direct_survey_scene import DirectSurveyScene

router = Router(name=__name__)

# ✅ Регистрируем ВСЕ хэндлеры и внутренние роутеры сцен в правильном порядке
router.include_routers(
    admin_router,
    test_router,
    survey_starter_router,  # Он поймает самый первый клик "start_pool_click:"
    # direct_survey_router,  # Он будет ловить внутренние клики сцены "survey_ans:"
)

# Регистрируем стартовые точки входа для остальных сцен
router.callback_query.register(
    RegistrationScene.as_handler(),
    F.data == "registration"
)

router.message.register(
    BroadcastScene.as_handler(),
    Command("broadcast")
)

router.message.register(
    LoadPoolJsonScene.as_handler(),
    Command("create_pool")
)

router.message.register(
    CompleteSurvey.as_handler(),
    Command("complete_a_survey")
)

router.callback_query.register(
    CompleteSurvey.as_handler(),
    F.data == "complete_a_survey"
)

router.include_routers(
    cancel_router,
    echo_router
)


# ✅ Обязательно добавляем класс новой сцены в список возвращаемых сцен!
def get_scenes() -> list[type[Scene]]:
    return [
        registration_scene.RegistrationScene,
        broadcast_text_scene.BroadcastScene,
        load_pool_json_scene.LoadPoolJsonScene,
        complete_a_survey_scene.CompleteSurvey,
        direct_survey_scene.DirectSurveyScene,  # Добавили сюда! 🔥
    ]
