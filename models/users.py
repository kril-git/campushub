from sqlalchemy import String, Enum, DateTime, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base
from models.mixin import Mixin
from services.EnumRoles import Roles


class User(Base, Mixin):
    uuid: Mapped[str] = mapped_column(String(100), unique=True)
    role: Mapped[Roles] = mapped_column(Enum(Roles), default=Roles.USER)
    first_name: Mapped[str] = mapped_column(String(50), unique=False, nullable=True)
    last_name: Mapped[str] = mapped_column(String(50), unique=False, nullable=True)
    last_visit: Mapped[DateTime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now()
    )
    language_code: Mapped[str] = mapped_column(String(5), unique=False, nullable=True)
    registration: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
