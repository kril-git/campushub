from sqlalchemy import String, Enum, Integer, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.mixin import Mixin
from services.EnumPools import PoolCategory
from services.EnumPoolAction import PoolAction


class Pool(Base, Mixin):
    pool_uuid: Mapped[str] = mapped_column(String(100), unique=True)
    pool_description: Mapped[str] = mapped_column(String(200), unique=False)
    pool_category: Mapped[PoolCategory] = mapped_column(Enum(PoolCategory), default=PoolCategory.ALL.name)
    pool_action: Mapped[PoolAction] = mapped_column(Enum(PoolAction), default=PoolAction.DELETE)

    poolquestion: Mapped[list["PoolQuestion"]] = relationship("PoolQuestion", back_populates="pool")

    def __str__(self):
        return (f"pool_id: {self.id}\n"
                f"pool_uuid: {self.pool_uuid}\n"
                f"pool_description: {self.pool_description}\n"
                f"pool_category: {self.pool_category}\n"
                f"pool_action: {self.pool_action}")


class PoolQuestion(Base, Mixin):
    pool_question_uuid: Mapped[str] = mapped_column(String(100), unique=False)
    pool_uuid: Mapped[str] = mapped_column(String(100), unique=False, nullable=True)
    question_number: Mapped[int] = mapped_column(Integer, unique=False, nullable=True)
    pool_question: Mapped[str] = mapped_column(String(200), unique=False)
    pool_id: Mapped[int] = mapped_column(ForeignKey("pools.id"))

    pool: Mapped["Pool"] = relationship("Pool", back_populates="poolquestion")
    poolanswer: Mapped[list["PoolAnswer"]] = relationship("PoolAnswer", back_populates="answer")

    def __str__(self):
        return (f"pool_question_uuid: {self.pool_question_uuid}\n"
                f"pool_uuid: {self.pool_uuid}\n"
                f"question_number: {self.question_number}\n"
                f"pool_question: {self.pool_question}\n"
                f"pool_id: {self.pool_id}\n")


class PoolAnswer(Base, Mixin):
    pool_answer_uuid: Mapped[str] = mapped_column(String(100), unique=False)
    pool_question_uuid: Mapped[str] = mapped_column(String(100), unique=False)
    answer_number: Mapped[int] = mapped_column(Integer, unique=False, nullable=True)
    pool_answer: Mapped[str] = mapped_column(String(200), unique=False, nullable=False)
    pool_question_id: Mapped[int] = mapped_column(ForeignKey("poolquestions.id"))

    answer: Mapped["PoolQuestion"] = relationship("PoolQuestion", back_populates="poolanswer")

    def __str__(self):
        return (f"pool_answer_id: {self.id}\n"
                f"pool_answer_uuid: {self.pool_answer_uuid}\n"
                f"pool_question_uuid: {self.pool_question_uuid}\n"
                f"answer_number: {self.answer_number}\n"
                f"pool_answer: {self.pool_answer}\n"
                f"pool_question_id: {self.pool_question_id}\n")


class UserPool(Base, Mixin):
    user_uuid: Mapped[str] = mapped_column(String(100), nullable=False)
    pool_id: Mapped[int] = mapped_column(Integer, unique=False, nullable=False)
    end_pool: Mapped[bool] = mapped_column(Boolean, default=False)
    step: Mapped[int] = mapped_column(Integer, unique=False, nullable=False)

    def __str__(self):
        return (f"user_uuid: {self.user_uuid}\n"
                f"pool_id: {self.pool_id}\n"
                f"end_pool: {self.end_pool}\n"
                f"step: {self.step}"
                )
