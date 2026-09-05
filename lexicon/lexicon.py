from dataclasses import dataclass


@dataclass
class LanguageTexts:
    """Класс для хранения текстов на одном языке"""
    start: str
    surname: str
    given_name: str
    middle_name: str
    phone: str
    email: str
    birth_date: str
    nationality: str
    term_time_address: str
    parents_info: str
    group: str


class Lexicon:
    # Использование:
    # LEXICON.RU.start  # "🎓 Добро пожаловать..."
    # LEXICON.EN.phone  # "📞 Enter your phone..."
    # LEXICON.get_text("RU", "start")  # "🎓 Добро пожаловать..."
    # LEXICON.get_start("EN")  # "🎓 Welcome..."
    RU: LanguageTexts = LanguageTexts(
        start="🎓 Добро пожаловать в систему регистрации!\n\n",
        surname="Введите вашу Фамилию:",
        given_name="Введите ваше имя:",
        middle_name="Введите ваше отчество:",
        group="Введите номер группы:",
        phone="📞 Введите ваш номер телефона в формате +7XXXXXXXXXX\nИли нажмите кнопку 'Отправить номер':",
        email="📧 Введите ваш Email (или напишите 'нет'):",
        birth_date="Дата рождения:",
        nationality="Ваша национальность:",
        term_time_address="Введите адресс места проживания в период учебы:",
        parents_info="Введите информацию о родителях .....",
    )
    EN: LanguageTexts = LanguageTexts(
        start="🎓 Welcome to the registration system!\n\n",
        surname="Введите вашу Фамилию:",
        given_name="Введите ваше имя:",
        middle_name="Введите ваше отчество:",
        group="Введите номер группы:",
        phone="📞 Введите ваш номер телефона в формате +7XXXXXXXXXX\nИли нажмите кнопку 'Отправить номер':",
        email="📧 Введите ваш Email (или напишите 'нет'):",
        birth_date="Дата рождения:",
        nationality="Ваша национальность:",
        term_time_address="Введите адресс места проживания в период учебы:",
        parents_info="Введите информацию о родителях .....",
    )

    @classmethod
    def get_text(cls, lang: str, key) -> str:
        """
                Получить текст по языку и ключу

                Args:
                    lang: Код языка ('RU' или 'EN')
                    key: Ключ текста

                Returns:
                    str: Текст на указанном языке
                """
        try:
            language = getattr(cls, lang.upper())
            return getattr(language, key)
        except (AttributeError, KeyError):
            # Если язык или ключ не найден - возвращаем текст на русском
            return getattr(cls.RU, key, f"❌ Текст '{key}' не найден")




LEXICON_ADMIN_HELP: dict[str, dict[str, str]] = {
    "RU": {
        "/create_admin": "сделать пользователя администратором",
        "/list_users": "получить список пользователей",
        # "/json_pool_load": "загрузить файл опроса",
        # "/complete_a_survey": "Пройти опрос",
        # "/list_users_pools": "Посмотреть список пользователей прошедших опрос",
        # "/list_users_answers": "Посмотреть ответ пользователя",

    },
    "EN": {
        "/create_admin": "create admin",
        "/list_users": "get users",
        # "/json_pool_load": "pool file load",
        # "/complete_a_survey": "go",
    }
}

LEXICON_USER_HELP: dict[str, dict[str, str]] = {
    "RU": {
        "/info": " - Общая информация."
    },
    "EN": {
    }
}

LEXICON_CANCEL: dict[str, str] = {
    "RU": "Отмена",
    "EN": "Cancel"
}

LEXICON_MAIN: dict[str, dict[str, str]] = {
    "RU": {
        "/ffmpeg": "выделить из видео аудио дорожку",
        "/redis": "основные команды",
        "/alembic": "основное для работы",
        "/ChatActionSender": "как сделать typing.",
        "/vps": "конфигурация.",
    },
    "EN": {

    }
}

LEXICON_TEXT_REGISTRATION_START: dict[str, str] = {
    "RU": f"Вы перешли в раздел регистрации.\n\n"
          f"Регистрация займет некоторое время, если Вы им располагаете в данный момент и готовы,"
          f" нажмите НАЧАТЬ. Или ВЫХОД. 👇",
    "EN": "Cancel"
}

LEXICON_TEXT_REGISTRATION_STEP_0: dict[str, str] = {
    "RU": "Вам ",
    "EN": ""
}
