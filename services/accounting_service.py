import logging

from lexicon.lexicon_ru import LEXICON_ADD_PRODUCTS_PROCESS_FULL

logger = logging.getLogger(__name__)


def get_str_add_product(step: int) -> str | None:
    try:
        return f"Введите {LEXICON_ADD_PRODUCTS_PROCESS_FULL.get(step).get(step + 100)} товара."
    except KeyError:
        logger.info("Такого ключа в словаре нет.")
        return None
