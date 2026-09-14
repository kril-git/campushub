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


def render_reg_user(index: int, user: PersonalRecordCard) -> str:
    """
    Таблица personalrecordcard
    Возвращает index, uuid,surname, given_name, phone

    """
    return (
        f"{index}, {user.uuid}, {user.surname}, {user.given_name}, {user.phone}\n"
    )
