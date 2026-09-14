from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import connection
from models import PersonalRecordCard


async def _get_personal_record_short(
    session: AsyncSession,
) -> list[str]:
    result = await session.execute(
        select(
            PersonalRecordCard.uuid,
            PersonalRecordCard.surname,
            PersonalRecordCard.given_name,
            PersonalRecordCard.phone,
        )
    )
    rows = result.all()
    return [
        f"{i}, {uuid}, {surname}, {given_name}, {phone}\n"
        for i, (uuid, surname, given_name, phone) in enumerate(rows, start=1)
    ]


@connection
async def get_personal_record_short(session: AsyncSession) -> list[str]:
    return await _get_personal_record_short(session)