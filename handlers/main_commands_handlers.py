import logging
from asyncio import sleep

from aiogram import Router, flags
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.admin_crud import get_users_pools_join_user
from database.dao.base_repository import BaseRepository
from database.dao.pool_repository import DAOPools, PoolRepository
from lexicon.lexicon_ru import LEXICON_FFMPEG, LEXICON_REDIS, LEXICON_ALEMBIC, LEXICON_CHAT_ACTION_SENDER, LEXICON_VPS
from models import Pool
from services.EnumPools import PoolCategory
from services.ssh_service import SSH

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(Command(commands="ffmpeg"))
async def get_help_ffmpeg(message: Message):
    await message.answer(text=LEXICON_FFMPEG, parse_mode="HTML")


@router.message(Command(commands="redis"))
@flags.chat_action(action="typing", initial_sleep=2, interval=3)
async def ger_help_redis(message: Message):
    await message.answer(text=LEXICON_REDIS, parse_mode="HTML")


@router.message(Command(commands="alembic"))
async def ger_help_redis(message: Message):
    await message.answer(text=LEXICON_ALEMBIC, parse_mode="HTML")


@router.message(Command(commands="ChatActionSender"))
async def chat_action_sender(message: Message):
    await message.answer(text=LEXICON_CHAT_ACTION_SENDER)


@router.message(Command(commands="vps"))
async def vps_help(message: Message):
    await message.answer(text=LEXICON_VPS)


@router.message(Command(commands="test"))
async def test(message: Message):
    await message.answer(text=f"проверка функционала\n\n")

    # class PoolRepository(BaseRepository):
    #     """Репозиторий для работы с опросами (Pools)."""

    for i in range(100):
        if settings.VPS:
            with SSH(hostname=settings.DB_HOST_VDS,
                     username=settings.SSH_USERNAME,
                     password=settings.SSH_PASSWORD,
                     pkey=settings.SSH_PKEY_PATH,
                     port=22) as ssh:  # noob@10.0.1.**
                try:
                    out = ssh.exec_cmd('ls -al /var')
                    if out is  None:
                        print(f"tunnels ----------> нееееееееее поднят")

                    else:
                        print(f"tunnels ----------> поднят")
                except Exception as e:
                    print(f"tunnels")

        await sleep(10)
    # pool_repo = PoolRepository()
    # print(await PoolRepository.get_by_id(obj_id=52))
    # print(await pool_repo.get_by_id(obj_id=52))



    # data = await DAOPools.get_answer_by_user_id(user_uuid="7740157654")
    # for i in data:
    #     print(i)

    # print("================================")
    # data = await DAOPools.get_pool(category=PoolCategory.SALON)
    # print(data)
    # print(type(data))
    # print(data.id)
    # print(data.pool_description)
    #
    # # data = await DAOPools.get_pool_id_action(pool_category=PoolCategory.SALON)
    # print(f"------------   {data} --------- {type(data)}")
    # rec = await DAOPools.get_by_link_id(link_id=data.id)
    # print(rec)
    # print(type(rec))
    # for i in rec:
    #     print(i)
    # for i in data:
    #     print(i)
    # print("------------")
    # print(data[0])
    # content = as_list(
    #     as_marked_section(
    #         Bold("Success:"),
    #         "Test 1",
    #         "Test 3",
    #         "Test 4",
    #         marker="✅ ",
    #     ),
    #     as_marked_section(
    #         Bold("Failed:"),
    #         "Test 2",
    #         marker="❌ ",
    #     ),
    #     as_marked_section(
    #         Bold("Summary:"),
    #         as_key_value("Total", 4),
    #         as_key_value("Success", 3),
    #         as_key_value("Failed", 1),
    #         marker="  ",
    #     ),
    #     HashTag("#test"),
    #     sep="\n\n",
    # )
    # await message.answer(**content.as_kwargs())