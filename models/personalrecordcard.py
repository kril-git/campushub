from sqlalchemy import String, Enum, DateTime, func, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date, datetime
from sqlalchemy import Date

from services.EnumRoles import Roles

from models import Base
from models.mixin import Mixin


class PersonalRecordCard(Base, Mixin):
    uuid: Mapped[str] = mapped_column(String(100), unique=True)
    surname: Mapped[str] = mapped_column(String(30), unique=False)
    given_name: Mapped[str] = mapped_column(String(30), unique=False)
    middle_name: Mapped[str] = mapped_column(String(30), unique=False)
    phone: Mapped[str] = mapped_column(String(30), unique=False, nullable=True, default="")
    email: Mapped[str] = mapped_column(String(50), unique=False, nullable=True, default="")
    birth_date: Mapped[date] = mapped_column(Date, nullable=False, unique=False)
    nationality: Mapped[str] = mapped_column(String(30), unique=False, nullable=False)
    term_time_address: Mapped[str] = mapped_column(String(100), unique=False, nullable=False)
    parents_info: Mapped[str] = mapped_column(Text, unique=False, nullable=True)
    group: Mapped[str] = mapped_column(String(10), unique=False, nullable=True, default="Ээб-7")
    status_family: Mapped[str] = mapped_column(String(100), unique=False, nullable=True, default="")
    children: Mapped[str] = mapped_column(String(5), unique=False, nullable=True, default="")
    low_income_family: Mapped[str] = mapped_column(String(5), unique=False, nullable=True, default="")
    disability: Mapped[str] = mapped_column(String(5), unique=False, nullable=True, default="")
    brsm: Mapped[str] = mapped_column(String(5), unique=False, nullable=True, default="")
    cas: Mapped[str] = mapped_column(String(5), unique=False, nullable=True, default="")

    def __repr__(self):
        return f"<User(uuid={self.uuid}, surname={self.surname})>"
