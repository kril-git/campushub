import asyncio
import logging
from pathlib import Path
from typing import Dict

import asyncssh
from aiogram.exceptions import TelegramNetworkError

logger = logging.getLogger(__name__)


class TunnelManager:
    def __init__(
            self,
            ssh_host: str,
            ssh_user: str,
            ssh_key_path: str,
            ssh_port: int = 22,
            local_host: str = "localhost"
    ):
        self.ssh_host = ssh_host
        self.ssh_user = ssh_user
        self.ssh_port = ssh_port
        self.ssh_key_path = Path(ssh_key_path).expanduser()
        self.local_host = local_host

        self._conn: asyncssh.SSHClientConnection | None = None
        self._ssh_lock = asyncio.Lock()
        self._tunnels = []
        self._tunnel_configs: Dict[str, tuple] = {}
        self._closed = False

        logger.info(f"TunnelManager: {ssh_user}@{ssh_host}:{ssh_port}")

    async def connect_ssh(self) -> asyncssh.SSHClientConnection:
        if self._closed:
            raise RuntimeError("TunnelManager уже закрыт")

        async with self._ssh_lock:
            if self._conn and not self._conn.is_closed():
                return self._conn

            logger.info(f"🔌 Подключение к {self.ssh_user}@{self.ssh_host}...")

            try:
                self._conn = await asyncssh.connect(
                    host=self.ssh_host,
                    port=self.ssh_port,
                    username=self.ssh_user,
                    client_keys=[str(self.ssh_key_path)],
                    known_hosts=None,
                    keepalive_interval=30,
                    connect_timeout=10
                )
                logger.info("✅ SSH соединение установлено")
                return self._conn
            except TelegramNetworkError as e:
                logger.error(f"❌ Ошибка SSH. TelegramNetworkError: {e}")
                self._conn = None
                raise
            except OSError as e:
                logger.error(f"❌ [Errno 51] Network is unreachable: {e}")
                self._conn = None
                raise
            except asyncssh.Error as e:
                logger.error(f"❌ Ошибка SSH: {e}")
                self._conn = None
                raise
            except Exception as e:
                logger.error(f"❌ Неожиданная ошибка: {e}")
                self._conn = None
                raise

    async def forward_port(self, name: str, local_port: int, remote_host: str, remote_port: int):
        """Создаёт туннель и сохраняет конфиг для переподключения"""
        await self.connect_ssh()

        logger.info(f"🔗 Туннель '{name}': {self.local_host}:{local_port} -> {remote_host}:{remote_port}")

        try:
            tunnel = await self._conn.forward_local_port(
                self.local_host, local_port,
                remote_host, remote_port
            )
            self._tunnels.append(tunnel)
            self._tunnel_configs[name] = (local_port, remote_host, remote_port)
            logger.info(f"✅ Туннель '{name}' создан")
            return tunnel
        except Exception as e:
            logger.error(f"❌ Ошибка создания туннеля '{name}': {e}")
            raise

    async def _recreate_tunnels(self):
        """Пересоздаёт все туннели из сохранённых конфигов"""
        for name, config in self._tunnel_configs.items():
            local_port, remote_host, remote_port = config
            await self.forward_port(name, local_port, remote_host, remote_port)

    async def ssh_close(self):
        if self._conn and not self._conn.is_closed():
            try:
                self._conn.close()
                await self._conn.wait_closed()
            except Exception:
                pass
        self._conn = None

    async def reconnect(self):
        """Полное переподключение: SSH + все туннели"""
        logger.warning("🔄 Переподключение SSH и туннелей...")

        # 1. Закрываем старые туннели
        for tunnel in self._tunnels:
            try:
                tunnel.close()
            except asyncssh.Error as e:
                logger.warning(f"Ошибка при закрытии туннеля: {e}")
            except Exception as e:
                logger.error(f"Неожиданная ошибка при закрытии туннеля: {e}")
        self._tunnels.clear()

        # 2. Закрываем SSH
        await self.ssh_close()

        # 3. Подключаем SSH заново
        await self.connect_ssh()

        # 4. Пересоздаём туннели
        await self._recreate_tunnels()

        logger.info("✅ SSH и туннели переподключены")

    async def is_healthy(self) -> bool:
        """Проверка здоровья SSH соединения"""
        if not self._conn or self._conn.is_closed():
            return False
        try:
            await self._conn.run('echo "ping"', check=False)
            return True
        except asyncssh.Error:
            return False
        except Exception:
            return False

    async def close(self):
        if self._closed:
            return

        self._closed = True
        for tunnel in self._tunnels:
            try:
                tunnel.close()
            except asyncssh.Error as e:
                logger.warning(f"Ошибка при закрытии туннеля: {e}")
            except Exception as e:
                logger.error(f"Неожиданная ошибка при закрытии туннеля: {e}")
        self._tunnels.clear()
        await self.ssh_close()
        logger.info("✅ Все соединения закрыты")
