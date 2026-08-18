from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from models import Base
from models.mixin import Mixin


class Answer(Base, Mixin):
    user_uuid: Mapped[str] = mapped_column(String(100), nullable=False)
    pool_id: Mapped[int] = mapped_column(Integer, unique=False, nullable=False)
    question_id: Mapped[int] = mapped_column(Integer, unique=False, nullable=False)
    answer_id: Mapped[int] = mapped_column(Integer, unique=False, nullable=False)
    step: Mapped[int] = mapped_column(Integer, unique=False, nullable=False)

    def __str__(self):
        return (f"pool_id: {self.id}\n"
                f"user_uuid: {self.user_uuid}\n"
                f"pool_id: {self.pool_id}\n"
                f"question_id: {self.question_id}\n"
                f"answer_id: {self.answer_id}\n"
                f"step: {self.step}"
                )
