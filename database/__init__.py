# from .create_engine import engine
# import logging
from config import settings
# from .connection import connection
# from .db_helper import db_helper
#
# # logger = logging.getLogger(__name__)
# # __all__ = ("engine",
# #            "db_helper")
# __all__ = (
#            "db_helper", "connection"
# )

# tunnel_manager = AsyncTunnelManager()
#
# ssl_connect_kwargs = {
#     "host": settings.DB_HOST_VDS,
#     "port": settings.SSH_PORT,
#     "username": settings.SSH_USERNAME,
#     "keepalive_interval": 30,
#     "keepalive_count_max": 3,
#     "known_hosts": None,  # Для разработки, в проде используйте known_hosts
# }
# if settings.SSH_PKEY_PATH:
#     ssl_connect_kwargs["client_keys"] = [settings.SSH_PKEY_PATH]
# elif settings.SSH_PASSWORD:
#     ssl_connect_kwargs["password"] = settings.SSH_PASSWORD
# else:
#     raise ValueError("Neither SSH key nor password provided")
