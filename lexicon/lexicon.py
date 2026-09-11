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
    hello: str
    one_enter: str
    user_exist: str
    status_family: str
    children: str
    low_income_family: str
    disability: str
    brsm: str
    cas: str

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
        phone="📞 Введите ваш номер телефона в формате +375XXXXXXXXXX\nИли нажмите кнопку 'Отправить номер':",
        email="📧 Введите ваш Email (или напишите 'нет'):",
        birth_date="Дата рождения:",
        nationality="Ваше гражданство: пример - Республика Беларусь",
        term_time_address="Введите адресс места проживания в период учебы:",
        parents_info="Введите информацию о родителях (ФИО, Место работы, Должность, Контактный номер телефона)",
        hello="Привет {var}, рад тебя видеть 👋",
        one_enter="Привет, друг 👋.\n Поздравляем тебя 🎉 - ты "
                  "студент самого лучшего ВУЗа страны. Ну а "
                  "теперь пришло время познакомиться. На кнопке меню нажми получить список команд ➡️  /registration и "
                  "ответь на вопросы 🤔. У тебя это займет пару минут, но очень поможет "
                  "нам для дальнейшей коммуникации и дружбы 🤝.",
        user_exist="Если ты еще не прошел регистрацию, то перейди в меню ➡️ получить список команд ➡️ регистрация",
        status_family="Укажите статус своей семьи условными обозначениями: пол - полная семья, Р -родители в разводе, "
                      "П - потеря кормильца (одного из родителей), Б -воспитывает один из родителей, не состоящей в "
                      "браке",
        children="У тебя многодетная семья (3 и более детей до 18 лет) ? ответ в формате (да или нет)",
        low_income_family="У тебя малообеспеченная семья ? ответ в формате (да или нет)",
        disability="У тебя есть инвалидность ? ответ в формате (да или нет)",
        brsm="Являешься членом ПО ООО БРСМ?  ответ в формате (да или нет)",
        cas="Ты пострадавший от ЧАЭС ? ответ в формате (да или нет)",
    )
    # EN: LanguageTexts = LanguageTexts(
    #     start="🎓 Welcome to the registration system!\n\n",
    #     surname="Введите вашу Фамилию:",
    #     given_name="Введите ваше имя:",
    #     middle_name="Введите ваше отчество:",
    #     group="Введите номер группы:",
    #     phone="📞 Введите ваш номер телефона в формате +7XXXXXXXXXX\nИли нажмите кнопку 'Отправить номер':",
    #     email="📧 Введите ваш Email (или напишите 'нет'):",
    #     birth_date="Дата рождения:",
    #     nationality="Ваша национальность:",
    #     term_time_address="Введите адресс места проживания в период учебы:",
    #     parents_info="Введите информацию о родителях .....",
    #     hello='Hello {var}',
    #     one_enter="",
    #     user_exist="",
    #     status_family="",
    # )

    @classmethod
    def get_text(cls, key: str, lang: str = "RU") -> str:
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

    @classmethod
    def get_text_and_var(cls, key: str, lang: str = "RU", **kwargs) -> str:
        try:
            text = getattr(getattr(cls, lang.upper()), key)
            return text.format(**kwargs)
        except (AttributeError, KeyError):
            return getattr(cls.RU, key, f"❌ Текст '{key}' не найден").format(**kwargs)


LEXICON_ADMIN_HELP: dict[str, dict[str, str]] = {
    "RU": {
        "/create_admin": "сделать пользователя администратором",
        "/list_users": "получить список пользователей",
        "/export_users_to_exel": "создать файл зарегистрированных пользователей",

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
