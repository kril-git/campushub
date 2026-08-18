from sqlalchemy import DateTime, func, Integer
from sqlalchemy.orm import Mapped, mapped_column, declared_attr


class Mixin:

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + 's'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date_create: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()

    )
    date_update: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
