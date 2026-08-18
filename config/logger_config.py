import logging
import logging.config
import os
from pathlib import Path

import coloredlogs
import yaml

from core.config import settings

logger = logging.getLogger(__name__)


# Цвета ANSI
class Colors:
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'


class ColoredFormatter(logging.Formatter):
    """Форматтер с цветами для уровней логирования"""
    NAME_COLOR = '\033[96m'  # имя логгера - циан
    RESET = '\033[0m'
    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
        # Цвета для разных уровней
        self.level_colors = {
            logging.DEBUG: Colors.GREEN,
            logging.INFO: Colors.WHITE,
            logging.WARNING: Colors.YELLOW,
            logging.ERROR: Colors.RED,
            logging.CRITICAL: Colors.RED + Colors.BOLD,
        }

    def format(self, record):
        # Сохраняем оригинальный уровень
        original_levelname = record.levelname

        # Добавляем цвет к уровню
        color = self.level_colors.get(record.levelno, Colors.RESET)
        record.levelname = f"{color}{original_levelname}{Colors.RESET}"
        # 2. Красим ИМЯ ЛОГГЕРА (опционально)
        original_name = record.name
        record.name = f"{self.NAME_COLOR}{original_name}{self.RESET}"

        # Форматируем сообщение
        result = super().format(record)

        # Восстанавливаем оригинальный уровень (на всякий случай)
        record.levelname = original_levelname

        return result


def print_if_option_debug(message: str):
    if settings.APP_DEBUG:
        print(message)
    else:
        logger.setLevel(level="INFO")
        logger.info(f"Logging config: {logger.level}")


def set_base_config_loaders_as_default(default_level=logging.INFO):
    logging.basicConfig(
        filename="logs/app.log",
        level=default_level,
        format=settings.FORMAT_LOGGING,
        datefmt=settings.TIME_FORMAT_LOGGING,
    )
    coloredlogs.install(level=default_level)


def setup_logging(env_key="LOG_CFG"):
    """
    Настройка логирования из YAML файла
    # Уровни от DEBUG до CRITICAL
    logging.DEBUG     # 10 - Самое подробное (отладка)
    logging.INFO      # 20 - Обычная информация о работе
    logging.WARNING   # 30 - Предупреждения (что-то не так, но работает)
    logging.ERROR     # 40 - Ошибки (что-то сломалось, но приложение живо)
    logging.CRITICAL  # 50 - Критические ошибки (приложение может упасть)
    Важно: чем выше уровень, тем меньше сообщений будет записано.
    """

    path = os.getenv(
        env_key, settings.DEBUG_FILE_SETTINGS
    )  # возвращает значение ключа key переменной среды, если оно
    # существует или значение по умолчанию default, если его нет.

    print_if_option_debug(
        f"Используем файл конфигурации {settings.DEBUG_FILE_SETTINGS}"
    )

    # Определяем цвета для разных полей (какие части строки красить)
    field_styles = {
        'asctime': {'color': 'green'},  # время - зелёным
        'name': {'color': 'blue'},  # имя логгера - синим
        'levelname': {'color': 'cyan', 'bold': True},  # уровень - жирным цианом
        'filename': {'color': 'magenta'},  # имя файла - пурпурным
        'lineno': {'color': 'magenta'},  # номер строки - пурпурным
    }

    # Определяем цвета для уровней логирования
    level_styles = {
        'debug': {'color': 'green'},  # DEBUG - зелёный
        'info': {'color': 'white'},  # INFO - белый
        'warning': {'color': 'yellow'},  # WARNING - жёлтый
        'error': {'color': 'red'},  # ERROR - красный
        'critical': {'color': 'red', 'bold': True},  # CRITICAL - жирный красный
    }

    if os.path.exists(path):
        with open(path, "rt") as f:
            try:
                config = yaml.safe_load(f.read())
                # logging.config.dictConfig(config)  # Применяем конфигурацию
                # Добавляем цветной форматтер для консоли
                # if "handlers" in config and "console" in config["handlers"]:
                #     config["formatters"] = "colored"
                # if "formatters" not in config:
                #     config["formatters"] = {}
                # config['formatters']['colored'] = {
                #     # '()': ColoredFormatter,
                #     'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                #     'datefmt': '%Y-%m-%d %H:%M:%S'
                # }
                logging.config.dictConfig(config)  # Применяем конфигурацию

                print(f"----------------------------> {logging.getLogger()}")
            except Exception as e:
                set_base_config_loaders_as_default()
                logger.error(
                    f"Error in Logging Configuration. Using default configs. Path {path} not found. "
                    f"Exception -> {e}"
                )

        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)  # Создаем директорию для логов если ее нет
    else:
        set_base_config_loaders_as_default()
        logger.error("Error in Logging Configuration. Using default configs ")
