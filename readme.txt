Для развертывания проекта из моего шаблона нудно:

1. Дублируем папку проекта и переименовываем ее по имени нового проекта.

2. Удаляем папки .git .idea alembic

3. Инициализируйте локальный проект:

        git init
        git add .
        git commit -m "First commit"

4. Привязываем к GitHub:

        git remote add origin <ССЫЛКА_НА_ВАШ_РЕПОЗИТОРИЙ>
        git branch -M main
        git push -u origin main

    Или следуем инструкции на github которая доступна после создания проекта

5. При необходимости, создаем окружение venv:

        python -m venv .venv
        source <имя_окружения>/bin/activate
        deactivate

6. Создаем базу данных на VPS сервере или локально:

        ssh fincoin # заходим на удаленный сервер (в моем случае такая команда)
        sudo -i -u postgres
        psql
        SELECT * FROM pg_hba_file_rules; # посмотреть правила
        CREATE DATABASE <database_name>;
        CREATE DATABASE sales OWNER salesapp ENCODING 'UTF8' CONNECTION LIMIT 100; пример более сложной конфигурации
        \l список баз данных
        \c <database_name> при необходимости подключиться к бд
        \q выйти из psql

        ss -tunlp | grep 5432 # проверка порта
        ps aux | grep postgres

        \connect
        DELETE FROM имя_таблицы WHERE столбец = 'значение';
        update users set role='ADMIN' where id=1;
        select * from users;

7. Инициализируем Alembic:

        alembic нужно запускать в async режиме
        alembic init -t async alembic

        alembic revision --message="Initial" --autogenerate
        alembic upgrade head

    Если мы работаем через туннель то запускаем туннель из командной строки
        # ssh -L 0.0.0.0:5432:localhost:5432 postgres@155.212.171.8 -K /Users/kril/.ssh/id_ed25519_campushub
        ssh -L 0.0.0.0:5432:localhost:5432 -i /Users/kril/.ssh/id_ed25519_campushub postgres@155.212.171.8
        ssh -L [REMOTE_IP:]REMOTE_PORT:DESTINATION:DESTINATION_PORT [USER@]SSH_SERVER


    Если мы работаем через туннель то запускаем туннель из командной строки
        # ssh -L 0.0.0.0:5432:localhost:5432 postgres@62.169.26.93 -K /Users/kril/.ssh/ed25519_campushub
        ssh -L 0.0.0.0:5432:localhost:5432 -i /Users/kril/.ssh/ed25519_campushub kril@62.169.26.93
        ssh -L [REMOTE_IP:]REMOTE_PORT:DESTINATION:DESTINATION_PORT [USER@]SSH_SERVER


8. Postgres

    Конфигурационные файлы
        sudo nano /etc/postgresql/*/main/pg_hba.conf
        sudo nano /etc/postgresql/*/main/postgresql.conf
        Если статус не active (running), запустите её командой sudo systemctl start postgresql
        и добавьте в автозагрузку: sudo systemctl enable postgresql

logs


9.
        which python


пароль vds - Kril1966dzm

https://www.blast.hk/threads/205401/

https://pressanybutton.ru/post/aiogram/filtry-dlya-obrabotchikov-soobshenij-v-aiogram-3/


pip freeze > requirements.txt

alembic нужно запускать в async режиме
 alembic init -t async alembic


alembic revision --message="Initial" --autogenerate

alembic upgrade head

sqlalchemy.url = postgresql://postgres:postgres@192.168.100.53/sa -> alembric.ini

target_metadata = models.Base.metadata  -> env.pyc

# Удалить инлайн клавиатуру
await callback.message.edit_reply_markup(reply_markup=None)
await callback.message.delete_reply_markup()


https://ruvds.com/ru/vps_start/      https://habr.com/ru/companies/ruvds/articles/786014/
https://cloudvps.by

https://vc.ru/dev/1932737-luchshie-hostingi-dlya-telegram-botov-2025

https://www.youtube.com/watch?v=TaKqVvRCg0w
https://www.youtube.com/watch?v=INcuG3R5KDw


https://robotvasya.github.io/i18n-l10n-tutorial-aiogram/chapter_01.html - Интернационализация и Локализация.

    # https://firstvds.ru/technology/linux-user-management

Настройка VPS сервера:
Создать нового пользователя с правами SUDO
    ssh root@IP_АДРЕС
    adduser kril
    usermod -aG sudo kril
    """
    Флаг -a необходим, чтобы указанная группа не заменила множество других групп, в которых пользователь уже состоит.
    Флаг -G необходим для указания дополнительной группы, в которую будет добавлен пользователь.
    """
    su - kril
    whoami
    # https://timeweb.cloud/tutorials/ubuntu/sozdanie-novogo-polzovatelya-sudo-ubuntu
    # https://habr.com/ru/articles/964950/
    sudo nano /etc/group



Установим и запустим Redis-server:
    sudo apt install redis-server
    redis-cli
    127.0.0.1:6379> ping

Конфигурация sFtp пользователя: // при этом доступ по SSH не будет предоставлен (или SSH или sFTP)
    sudo nano /etc/ssh/sshd_config
    """
    добавить в конец
    """
    Match User sftp_download // можно Group вместо User
        ChrootDirectory /download
        ForceCommand internal-sftp
        AllowTcpForwarding no
        X11Forwarding no

    sshd -t // проверка конфига
    service sshd restart // рестарт

    # https://www.geraldonit.com/enabling-sftp-only-access-on-linux/

Создание собственной службы (systemd):

    # https://linux-notes.org/pishem-systemd-unit-fajl/
    # https://newadmin.ru/sozdanie-prostogo-systemd-unit/
    # https://timeweb.cloud/tutorials/linux/kak-ispolzovat-systemctl-dlya-upravleniya-sluzhbami-systemd

Шпаргалки
    # https://valynkin.ru/nastrojka-istorii-komand-v-bash.html


Postgresql
    Проверка синтаксиса через pg_ctl перед перезагрузкой:
        sudo -u postgres pg_ctl -D /var/lib/postgresql/16/main/ reload -t 5  // не находит такую команду
    перезагрузите PostgreSQL:
        sudo systemctl reload postgresql
    зайти в psql:
        sudo -i -u postgres
        psql
        SELECT * FROM pg_hba_file_rules; // посмотреть правила

    # https://docs.arenadata.io/ru/ADPG/current/how-to/pg-hba.html   Обзор конфигурации PG_HBA
    ss -tunlp | grep 5432
    ps aux | grep postgres

    Для проверки порта 5432
    nc -zv 127.0.0.1 5432
    nc -zv 155.212.171.8 6379
    lsof -i | grep 55555

Настройка входа через SSH без пароля
    ssh-keygen -t rsa
    cd ~/user/.ssh/
    ssh-copy-id -i my_id.pub user@111.11.11.11
    ssh-copy-id -i my_id.pub admin@37.46.133.233

    ~/.ssh/config :
    Host work
        HostName 123.45.67.89
        Port 12345
        User
        IdentityFile ~/.ssh/id_rsa_work
        IdentitiesOnly yes

    host github
        HostName github.com
        IdentityFile ~/.ssh/id_rsa_github
        User git
        IdentitiesOnly yes


    ssh firstvps_admin

Настройка ssh для github

    Откройте терминал
    Вставьте это и нажмите Enter: ssh-keygen

    Введите "cat *" где * - это путь
    Перейдите на веб-страницу Github, войдите в свой профиль,
     откройте Настройки, в разделе Access (Доступ) на левой боковой панели найдите SSH
     and GPG keys (SSH и GPG ключи), New SSH key (Новый SSH ключ) зеленого цвета, вставьте SSH ключ


    Маска файлов:

    4 - чтение
    2 - запись
    1 - выполнение
    Складываем необходимые пункты для получения конечной цифры, для "владельца", "группы владельцев" и "остальных" по отдельности. Получены е 3 цифры составляем в 3-х значное число например:
    chmod 777 test.txt
    У файла теперь полный доступ для "владельца" , "группы владельцев" и "остальных", т. к. 7=4+2+1
    chmod 700 test.txt

    или

    u - владелец файла;
    g - группа файла;
    o - другие пользователи.

    chmod ugo+rwx test5
    chmod go-rwx test5


Создание окружения venv:
    Выполните команду: $ python -m venv .venv
    macOS/Linux: source <имя_окружения>/bin/activate
    deactivate

git
    $ git rm --cached readme.txt //не отслеживать файл
    $ git status -s

bash
    # https://habr.com/ru/companies/ruvds/articles/325522/
    # https://www.opennet.ru/docs/RUS/bash_scripting_guide/
    # https://firstvds.ru/technology/osnovnye-komandy-linux


Беспрерывная работа бота
    nano /lib/systemd/system/fonlinebot.service
    # https://pythonru.com/primery/deploj-telegram-bota-na-vps
    # https://www.dmosk.ru/miniinstruktions.php?mini=python-ubuntu


Systemd: полное руководство для админов + примеры
    # https://habr.com/ru/articles/942760/
    # https://habr.com/ru/companies/timeweb/articles/824146/
    # https://hmarketing.ru/blog/server/chto-takoe-sluzhby-unit-v-linux/

psql
    # https://www.oslogic.ru/knowledge/598/shpargalka-po-osnovnym-komandam-postgresql/

netstat
    # https://putty.org.ru/articles/netstat-linux-examples

pg_dump
    # https://beget.com/ru/kb/how-to/rezervnoe-kopirovanie-i-vosstanovlenie-postgresql

    Чтобы сохранить только данные:
        -a или --data-only
        pg_dump -a -U ваш_пользователь -d ваша_база_данных -f только_данные.sql
            -c или --clean: Добавляет команды DROP TABLE перед INSERT, полезно при восстановлении в существующую базу.
            -t таблица_1 (или --table=таблица_1): Выгрузить данные только для конкретной таблицы.
            -T таблица_2 (или --exclude-table=таблица_2): Исключить данные из определенной таблицы.

        pg_dump --data-only -U postgres -d helper -T alembic_version
        psql -U postgres -d helper < /back/only_data.sql

es -d fincoin -T alembic_version -f /var/lib/postgresql/data/data_only_fincoin

--> pg_dump  -Fc -c -U postgres -d fincoin -T alembic_version -f /var/lib/postgresql/data/data_only_fincoin.bin
--> pg_restore  -c -U postgres -d fincoin /var/lib/postgresql/data/data_only_fincoin.bin

psql
    \connect
    DELETE FROM имя_таблицы WHERE столбец = 'значение';
    update users set role='ADMIN' where id=1;
    select * from users;


postgres смена пароля
    /etc/postgresql/#.#/main/pg_hba.conf
    # TYPE  DATABASE        USER            ADDRESS                 METHOD
    local   all             postgres                                trust

    sudo service postgresql restart

    sudo -u postgres psql
    ALTER USER postgres PASSWORD 'your_new_password';
    \q
    вернуть назад метод (METHOD)


@sampasabeDeployTestBot
sampasabe_deploy_test_bot
7481082226:AAEIpuQ9lF0jRmzgr4tA3jipwuKJijYHJos

git rm --cached <имя_файла>, а затем добавить файл в .gitignore


Systemd: полное руководство для админов + примеры
    # https://habr.com/ru/articles/942760/




1. Hidden Orchestra - Undergrowth [06:04]
02. Fogh Depot - Dark Side Of The M0Nk [05:59]
03. Gamardah Fungus - Hidden By The Leaves [08:14]
04. Bugge Wesseltoft & Dan Berglund & Henrik Schwarz - Valiant [07:37]
05. Dathon - Testing Moneo [04:40]
06. Trigg & Gusset - Desert Wind [05:23]
07. Fogh Depot - Anticyclone [06:42]
08. Ulrich Drechsler Cello Quartet - Our Source [05:42]
09. North Atlantic Drift - Albatross [05:53]
10. Zenjungle & Tunedin52 - Walking Into The Setting Sun [08:10]
11. Somewhere Off Jazz Street - When The Livin Ain't Easy [09:02]
12. Paul Pritchard - Gumshoe Blues [03:06]
13. Bohren & Der Club Of Gore - Maximum Black [07:35]
14. Marilyn Crispell & David Rothenberg - Tsering [04:55]
15. Nils Petter Molvaer - Song Of Sand 2 [06:11]
16. David Toop - Black Chamber [03:00]
17. Jun Miyake - Merry Widow [05:41]
18. Dale Cooper Quartet & The Dictaphones - Aucun Cave [06:49]
19. Joel Fausto & Illusion Orchestra - Radio Silence [06:27]
20. Shadowdream - Theological Agnosia [06:48]
21. Aivoaula - Oqubounce [05:18]
22. Black Chamber - Red Dawn [06:03]
23. Trigg & Gusset - Black Ocean [05:17]
24. Bohren & Der Club Of Gore - Constant Fear [06:24]
25. Zenjungle & Tunedin52 - We 'll Return To Another Place [08:19]
26. The Kilimanjaro Darkjazz Ensemble - Symmetry Of 6’S [04:38]
27. The Orchestra Of Mirrored Reflections - Leaving Big Sigh Of City Behind... [07:20]
28. Nektarios Manaras - Three Sketches Of Meteora [07:40]
29. Schwarzeneggerization - Deer At Log Cabin [03:24]
30. Splashgirl - Reducer [06:46]


https://habr.com/ru/articles/804263/   SSH-Туннели простыми словами

Основные способы освобождения порта:
Через Терминал (самый эффективный способ):
Откройте «Терминал».
Введите команду, чтобы найти PID (ID процесса) порта (замените 3000 на ваш порт):
lsof -i :3000
Убейте процесс, используя его PID:
kill -9 <PID>


https://3.jetbra.in

https://habr.com/ru/companies/amvera/articles/850470/

@t_ed_bot
@CEO_Helper
7251210806:AAEFXNlAWwLj3edXDx9Csy_FrcxyPSMCR7M


pyright какая то библиотека для контроля типов


Основные команды xattr
Удалить атрибут карантина (основное решение):
sudo xattr -rd com.apple.quarantine /путь/к/приложению
Очистить все атрибуты рекурсивно:
sudo xattr -cr /путь/к/приложению
Просмотреть атрибуты файла:
xattr -l /путь/к/файлу


sudo chflags -R nouchg #снимает атрибут защиты файла рекурсивно