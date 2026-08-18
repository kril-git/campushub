__all__ = ("router")

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.scene import Scene

from handlers.base_handlers import router as echo_router
from handlers.admin_handlers import router as admin_router
from handlers.set_user_to_admin_handler import router as set_user_to_admin_handler
from handlers.main_commands_handlers import router as main_commands_handlers
from handlers.accounting_handlers import router as accounting_router
from scenes.settings_scene import router as scene_router
from scenes import settings_scene
from scenes.accounting_products import router as accounting_scene_router
from scenes import accounting_products
from scenes.accounting_category import router as accounting_category_router
from scenes.load_pool_json_scene import router as pool_load_router, LoadPoolJsonScene
from scenes import accounting_category
from scenes import load_pool_json_scene
from scenes import complete_a_survey_scene
from scenes.complete_a_survey_scene import router as complete_a_survey_router

router = Router(name=__name__)

# pool_router = pool_load_router.message.register(LoadPoolJsonScene.as_handler(), Command("load_pool_json_scene"))
router.include_routers(admin_router,
                       accounting_router,
                       scene_router,
                       pool_load_router,
                       complete_a_survey_router,
                       accounting_scene_router,
                       set_user_to_admin_handler,
                       main_commands_handlers,
                       accounting_category_router,
                       echo_router,
                       )


def get_scenes() -> list[type(Scene)]:
    return [
        settings_scene.SettingsScene,
        accounting_products.AccountingProductsScene,
        accounting_category.AccountingCategoryScene,
        load_pool_json_scene.LoadPoolJsonScene,
        complete_a_survey_scene.CompleteSurvey

    ]

# def get_routers() -> list[Router]:
#     return [
#         settings_scene.router
#     ]
