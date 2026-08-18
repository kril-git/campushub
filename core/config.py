from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    ALCHEMY_ECHO: bool
    ALCHEMY_POOL_SIZE: int
    ALCHEMY_MAX_OVERFLOW: int
    BOT_TOKEN: str
    BOT_NAME: str
    DEBUG_FILE_SETTINGS: str
    APP_DEBUG: bool
    FORMAT_LOGGING: str
    TIME_FORMAT_LOGGING: str
    ADMINS: list[str]
    COMMAND_MENU: dict[str, str]
    SEND_MAILING_ALL: bool
    TRINITY_GROUP_CHAT_ID: str
    PATH_FOR_TEMP_FILES: str
    PATH_FOR_ALL_MEDIA_FILES: str = ""

    MAIN_ADMIN: str
    LOCALHOST: str
    PG_PORT: int
    SSH_INT_PORT: int

    # VPS: bool
    USE_TUNNEL: bool

    # Подключение к удаленной БД
    DB_USER_VDS: str
    DB_PASS_VDS: str
    DB_HOST_VDS: str

    # === PostgresSQL ===
    DB_TYPE: str
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str
    DB_ECHO: bool

    SSH_PORT: int
    SSH_USERNAME: str
    SSH_PASSWORD: str
    SSH_PKEY_PATH: str

    REDIS_DB_HOST: str
    REDIS_USERNAME: str | None = None
    REDIS_PASSWORD: str | None = None
    REDIS_PORT: int
    USE_REDIS: bool

    PASSWORDS: str | None

    # @property
    # def DATABASE_URL(self):
    #     return f"{self.DB_TYPE}+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    #
    @property
    def DATABASE_URL(self):
        if self.USE_TUNNEL:
            return (
                f"{self.DB_TYPE}+asyncpg://{self.DB_USER_VDS}:{self.DB_PASS_VDS}"
                f"@{self.LOCALHOST}:{self.DB_PORT}/{self.DB_NAME}"
            )
        else:
            return (
                f"{self.DB_TYPE}+asyncpg://{self.DB_USER}:{self.DB_PASS}"
                f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
                )

    @property
    def get_redis_url(self) -> str:
        if self.USE_TUNNEL:
            return f"localhost"
        else:
            return f"{self.DB_HOST}"

    @property
    def database_url_vds_server(self):
        return f"{self.DB_TYPE}+asyncpg://{self.DB_USER_VDS}:{self.DB_PASS_VDS}@{self.LOCALHOST}:{self.DB_PORT}/{self.DB_NAME}"

    # case_sensitive=True -> должен совпадать регистр букв
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )


settings = Settings()
