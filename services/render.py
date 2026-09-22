from models import User, PersonalRecordCard


def render_users(index: int, user: User) -> str:
    """
    Возвращает index, uuid, first_name, role
    Таблица users
    """
    return (
        f"{index}, {user.uuid}, {user.first_name}, "
        f"{user.role.name}, {user.registration}\n"
    )


def render_personal_record(index: int, row: tuple[str, str, str, str]) -> str:
    """
    Таблица personalrecordcard
    Возвращает index, uuid,surname, given_name, phone

    """
    uuid, surname, given_name, phone = row
    return (
        f"{index}, {uuid}, {surname}, {given_name}, {phone}\n"
    )
