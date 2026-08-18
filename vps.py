from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import asyncio

from sshtunnel import SSHTunnelForwarder

from database.db_helper import db_helper
from core.config import settings


def connection_local(method):
    async def wrapper(*args, **kwargs):
        async with db_helper.session_factory() as session:
            try:
                return await method(*args, session=session, **kwargs)
            except Exception as e:
                await session.rollback()
                print(e)
                raise e
            finally:
                await session.close()

    return wrapper


def connection(method):
    """
    Декоратор для установки соединения с базой данных.
    VPS = True, подключить удаленную БД, иначе локальную
    Подключение к удаленной БД происходит через SSH туннель
    """

    async def wrapper(*args, **kwargs):
        if settings.VPS:
                server = SSHTunnelForwarder(
                        ssh_address_or_host=(settings.DB_HOST_VDS, settings.SSH_INT_PORT),
                        ssh_username=settings.SSH_USERNAME,
                        ssh_password=settings.SSH_PASSWORD,
                        ssh_pkey=settings.SSH_PKEY_PATH,
                        # local_bind_address=(settings.LOCALHOST, settings.SSH_INT_PORT),
                        remote_bind_address=(settings.DB_HOST_VDS, settings.PG_PORT),

                )
                server.check_tunnels()

                #server.start()

                print(f"{settings.DB_HOST_VDS}, {settings.LOCALHOST}, {settings.PG_PORT}, {settings.SSH_PKEY_PATH}")
                print(f"SSH Tunnel established on local port {server.is_active}, {server.local_bind_port}")

                # server.start()
                print('Server connected via SSH')
                local_port = str(server.local_bind_port)
                print(server.local_bind_port)
                async with db_helper.session_factory() as session:
                    try:
                        return await method(*args, session=session, **kwargs)
                    except Exception as e:
                        await session.rollback()
                        print(e)
                        raise e
                    finally:
                        # await session.close()
                        print("server close")
        else:
            async with db_helper.session_factory() as session:
                try:
                    return await method(*args, session=session, **kwargs)
                except Exception as e:
                    await session.rollback()
                    print(e)
                    raise e
                finally:
                    await session.close()

    return wrapper


class DatabaseHelperLocal:
    def __init__(self):
        self.engine = create_async_engine(
            url=settings.DATABASE_URL, echo=settings.DB_ECHO
        )

        self.session_factory = async_sessionmaker(
            bind=self.engine, autoflush=False, autocommit=False, expire_on_commit=False
        )


class DatabaseHelperVPS:
    def __init__(self):
        self.engine = create_async_engine(
            url=settings.database_url_vds_server,
            echo=settings.DB_ECHO
        )

        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False
        )


class DatabaseHelper:
    """
    Класс DatabaseHelper.
    Создаёт движок и сессию.
    Если settings.VPS = TRUE, то класс создаст подключение к VPS серверу,
    иначе к локальному.
    """

    def __init__(self):
        if settings.VPS:
            self.engine = create_async_engine(
                url=settings.database_url_vds_server,
                echo=settings.DB_ECHO
            )
            print(settings.database_url_vds_server)

            self.session_factory = async_sessionmaker(
                bind=self.engine,
                autoflush=False,
                autocommit=False,
                expire_on_commit=False
            )
        else:
            self.engine = create_async_engine(
                url=settings.DATABASE_URL, echo=settings.DB_ECHO
            )

            self.session_factory = async_sessionmaker(
                bind=self.engine,
                autoflush=False,
                autocommit=False,
                expire_on_commit=False
            )


# @connection
# async def select_all(session: AsyncSession):
async def select_all():
    db_helper = DatabaseHelper()
    server = SSHTunnelForwarder(
        ssh_address_or_host=(settings.DB_HOST_VDS, settings.SSH_PORT),
        ssh_username=settings.SSH_USERNAME,
        ssh_password=settings.SSH_PASSWORD,
        ssh_pkey=settings.SSH_PKEY_PATH,
        ssh_config_file=None,
        remote_bind_address=("0.0.0.0", settings.PG_PORT),
        local_bind_address=(settings.LOCALHOST, settings.PG_PORT),
        allow_agent=False
    )
    print(server.check_tunnels())

    server.start()
    print(f"Tunnel is {server.is_active} {server.tunnel_is_up} ")

    print(f"{settings.DB_HOST_VDS}, {settings.LOCALHOST}, {settings.PG_PORT}, {settings.SSH_PKEY_PATH}")
    print(f"SSH Tunnel established on local port {server.is_active}, {server.local_bind_port}")

    # server.start()
    print('Server connected via SSH')
    user_input = input("Enter something: ")
    print("You entered: " + user_input)
    server.close()

    query = 'SELECT * FROM users'
    # test = await session.execute(text(query))
    # for row in test:
    #     print(row)
    # print(test.scalars().all())


if __name__ == "__main__":
    asyncio.run(select_all())

