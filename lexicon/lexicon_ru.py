LEXICON_MENU_USER: dict[str, str] = {
    "/start": "запустить сеанс.",
    # "/accounting": "управленческий учет",
    "/help": "получить список команд."
}

LEXICON_MENU_ADMIN: dict[str, str] = {
    "/start": "запустить сеанс.",
    "/accounting": "управленческий учет",
    "/settings": "настройки",
    # "/main": "меню помощника",
    "/help": "получить список команд администратора."
}

LEXICON_ADMIN_HELP: dict[str, str] = {
    "/create_admin": "сделать пользователя администратором",
    "/list_users": "получить список пользователей"
}

LEXICON_DIRECTORIES: dict[str, str] = {
    "/products": "справочник товаров",
    "/invoice": "счета",
    "/waybill": "накладные",
}

LEXICON_DIRECTORIES_SCENE: dict[str, str] = {
    "products": "СПРАВОЧНИК ТОВАРОВ",
    "category": "СПРАВОЧНИК КАТЕГОРИЙ",
    "invoice": "СЧЕТА",
    "waybill": "НАКЛАДНЫЕ",
    "exit": "ВЫХОД",
}

LEXICON_ADD_PRODUCTS: str = (f"<b>В этом разделе можно добавить новые товары или услуги</b>\n"
                             f"<i>Вам будут заданы вопросы в следующей последовательности</i>\n\n"
                             f"     Наименование товара\n"
                             f"     Описание товара\n"
                             f"     Категория товара\n"
                             f"     Стоимость товара. Формат 0.99 что означает 99 копеек\n"
                             )

LEXICON_ADD_PRODUCTS_PROCESS: dict[int, str] = {
    1: "product",
    2: "description",
    3: "category",
    4: "price",
}

LEXICON_ADD_PRODUCTS_PROCESS_FULL: dict[int, dict[int, str]] = {
    1: {1: "product", 101: "наименование"},
    2: {2: "description", 102: "описание"},
    3: {3: "category", 103: "категория"},
    4: {4: "price", 104: "стоимость"},
}

LEXICON_CANCEL: str = "Отмена"

LEXICON_FFMPEG: str = (f"<i>Отделить аудио от видео(без конвертации)</i>\n"
                       f"<pre>ffmpeg -i input_file_with_aac_audio.mp4 -c:a copy aac.aac</pre>\n"
                       f"<i>Аудио конвертировать</i>\n"
                       f"<pre>>ffmpeg -i aac.aac mp3.mp3</pre>")

LEXICON_REDIS: str = (f"<i>Подключитесь к Redis Изнутри контейнера (через redis-cli)</i>\n"
                      f"<pre>docker exec -it my-redis redis-cli</pre>\n\n"
                      f"<b>Поддерживаемые команды</b>\n"
                      f"<b>DEL</b> <i> - удалить ключ;</i>\n"
                      f"<b>EXISTS</b> <i>– определить, существует ли ключ;</i>\n"
                      f"<b>KEYS</b> <i>– найти все ключи, соответствующие заданному шаблону;</i>\n"
                      f"<b>PEXPIREAT</b> <i>– задать срок действия ключа в качестве временной метки Unix в "
                      f"миллисекундах;</i>\n"
                      f"<b>EXPIRE</b> <i>– задать срок действия ключа в секундах;</i>\n"
                      f"<b>EXPIREAT</b> <i>– задать срок действия ключа в качестве временной метки Unix в "
                      f"секундах;</i>\n"
                      f"<b>EXPIRETIME</b> <i> – получить временную метку Unix истечения срока действия для ключа;</i>\n"
                      f"<b>PERSIST</b> <i>– удалить даты истечения срока действия ключа;</i>\n"
                      f"<b>PEXPIRE</b> <i> – задать срок действия ключа в миллисекундах;</i>\n"
                      f"<b>PEXPIRETIME</b> <i>– получить временную метку Unix истечения срока действия для ключа в "
                      f"миллисекундах;</i>\n"
                      f"<b>PTTL</b> <i>– получить оставшийся срок действия ключа в миллисекундах;</i>\n"
                      f"<b>TTL</b> <i>– получить оставшийся срок действия ключа в секундах;</i>\n"
                      f"<b>SCAN</b> <i>– итерация по набору ключей в базе данных, выбранной в текущий момент.</i>\n\n"
                      f"<a href='https://www.tarantool.io/ru/tarantooldb-resp/doc/latest/overview/'>все команды без "
                      f"примеров</a>\n"
                      )

LEXICON_ALEMBIC: str = (f"<b>alembic</b><i> - нужно запускать в async режиме</i>\n"
                        f"<pre>alembic init -t async alembic</pre>\n\n"
                        f"<i>Сгенерировать скрипты обновления базы</i>\n"
                        f"<pre>alembic revision --message='Initial' --autogenerate</pre>\n\n"
                        f"<i>Накатить изменения на базу данных</i>\n"
                        f"<pre>alembic upgrade head</pre>\n"
                        f"<b>sqlalchemy.url = postgresql://postgres:postgres@192.168.100.53/sa -> alembric.ini</b>\n"
                        f"<b>target_metadata = models.Base.metadata  -> env.pyc</b>\n"
                        )

LEXICON_CHAT_ACTION_SENDER: str = (f"<b>Ссылка на документацию.\n\n</b>"
                                   f"<a href='https://docs.aiogram.dev/en/latest/utils/chat_action.html#usage'>Ссылка "
                                   f"на документацию.</a>"
                                   )

LEXICON_VPS: str = (f"<i>Подключаемся к VPS</i>\n"
                    f"<pre>ssh root@IP_АДРЕС</pre>\n"
                    f"<i>создаем пользователя с правами SUDO</i>\n"
                    f"<pre>adduser admin, \nusermod -aG sudo admin</pre>\n"
                    f"<i>Флаг -a необходим, чтобы указанная группа не заменила множество других групп, в которых "
                    f"пользователь уже состоит.</i>\n"
                    f"<i>Флаг -G необходим для указания дополнительной группы, в которую будет добавлен "
                    f"пользователь.</i>\n"
                    f"<i>проверка</i>\n"
                    f"<code>su - admin, whoami</code>\n"
                    f"<i>Статьи</i>\n"
                    f"<a href='https://timeweb.cloud/tutorials/ubuntu/sozdanie-novogo-polzovatelya-sudo-ubuntu'>Ссылка "
                    f"на документацию.</a>\n"
                    f"<a href='https://habr.com/ru/articles/964950/'>Ссылка "
                    f"на документацию.</a>\n\n"
                    f"<b>Настройка ssh для github</b>\n"
                    f"<pre>ssh-keygen</pre>\n"
                    f"<pre>cat ~/.ssh/файл публичного ключа</pre>\n"
                    f"<i>копируем ключ, и идем в GITHUB</i>\n"
                    f"<i>Настройки, в разделе Access (Доступ) на левой боковой панели найдите SSH и GPG ключи, "
                    f"New SSH key (Новый SSH ключ) зеленого цвета, вставьте SSH ключ</i>\n"
                    )
