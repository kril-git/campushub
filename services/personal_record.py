# services/personal_record.py
from database.dao.personal_record_repository import PersonalRecordDAO
from services.render import render_personal_record


async def get_personal_record_short_lines() -> list[str]:
    """Возвращает отформатированные строки для Telegram."""
    rows = await PersonalRecordDAO.get_short()
    return [
        f"{i}, {uuid}, {surname}, {given_name}, {phone}\n"
        for i, (uuid, surname, given_name, phone) in enumerate(rows, start=1)
    ]


async def get_personal_record_short_lines_render() -> list[str]:
    """
    Пример распаковки используя рэндер
    """
    rows = await PersonalRecordDAO.get_short()
    return [
        render_personal_record(i, row)
        for i, row in enumerate(rows, start=1)
    ]
