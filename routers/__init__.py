__all__ = ("router")

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.scene import Scene

from handlers.base_handlers import router as echo_router
from handlers.admin_handlers import router as admin_router
# from handlers.set_user_to_admin_handler import router as set_user_to_admin_handler
# from handlers.main_commands_handlers import router as main_commands_handlers
# from handlers.accounting_handlers import router as accounting_router
from scenes.settings_scene import router as scene_router
from scenes import settings_scene
# from scenes.accounting_products import router as accounting_scene_router
from scenes import accounting_products
# from scenes.accounting_category import router as accounting_category_router
# from scenes.load_pool_json_scene import router as pool_load_router, LoadPoolJsonScene
from scenes import accounting_category
from scenes import load_pool_json_scene
from scenes import complete_a_survey_scene
from scenes import registration_scene
from scenes.registration_scene import router as registration_router, RegistrationScene
from scenes.broadcast_text_scene import router as broadcast_text_router, BroadcastScene
from scenes import broadcast_text_scene

# from scenes.complete_a_survey_scene import router as complete_a_survey_router

router = Router(name=__name__)

# ✅ Возвращаем роутер с командой
# def get_routers() -> Router:
#     """Возвращает роутер с командой /registration"""
#     router_s = Router(name="registration_router")
#
#     # Регистрируем команду
#     router_s.message.register(
#         RegistrationScene.as_handler(),
#         Command("registration")
#     )
#
#     # Можно зарегистрировать дополнительные команды
#     router_s.message.register(
#         RegistrationScene.as_handler(),
#         Command("reg")  # Альтернативная команда
#     )
#
#     return router_s


router.include_router(
    admin_router,
    # registration_router,
    # broadcast_text_router,
    # echo_router,
)

router.message.register(
    RegistrationScene.as_handler(),
    Command("registration")
)

router.message.register(
    BroadcastScene.as_handler(),
    Command("broadcast")
)

router.include_router(echo_router)


def get_scenes() -> list[type(Scene)]:
    return [
        registration_scene.RegistrationScene,
        broadcast_text_scene.BroadcastScene,

    ]
