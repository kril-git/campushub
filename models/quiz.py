from datetime import date, datetime

from sqlalchemy import (
    String, Text, Integer, Boolean, Date, DateTime,
    ForeignKey, Enum, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.mixin import Mixin
from services.EnumQuizStatus import QuizStatus


class Quiz(Base, Mixin):
    """Квиз — набор вопросов с правильными ответами."""

    uuid: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[QuizStatus] = mapped_column(
        Enum(QuizStatus), default=QuizStatus.DRAFT, nullable=False, index=True,
    )
    show_correct_after_answer: Mapped[bool] = mapped_column(Boolean, default=True)
    show_result_to_user: Mapped[bool] = mapped_column(Boolean, default=True)

    # задел на будущее
    time_limit_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pass_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attempts_allowed: Mapped[int] = mapped_column(Integer, default=1)

    created_by: Mapped[str] = mapped_column(String(100), nullable=False)

    questions: Mapped[list["QuizQuestion"]] = relationship(
        "QuizQuestion", back_populates="quiz", cascade="all, delete-orphan",
    )
    responses: Mapped[list["QuizResponse"]] = relationship(
        "QuizResponse", back_populates="quiz", cascade="all, delete-orphan",
    )
    users: Mapped[list["QuizUser"]] = relationship(
        "QuizUser", back_populates="quiz", cascade="all, delete-orphan",
    )

    def __str__(self):
        return f"Quiz(id={self.id}, title={self.title}, status={self.status.value})"


class QuizQuestion(Base, Mixin):
    """Вопрос квиза."""

    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizs.id", ondelete="CASCADE"))
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(String(500), nullable=False)
    type: Mapped[str] = mapped_column(String(20), default="single", nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # задел на будущее
    points: Mapped[int] = mapped_column(Integer, default=1)
    image_file_id: Mapped[str | None] = mapped_column(String(200), nullable=True)

    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="questions")
    answers: Mapped[list["QuizAnswer"]] = relationship(
        "QuizAnswer", back_populates="question", cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("quiz_id", "number", name="uq_quizquestion_quiz_number"),
    )

    def __str__(self):
        return f"QuizQuestion(id={self.id}, number={self.number})"


class QuizAnswer(Base, Mixin):
    """Вариант ответа."""

    question_id: Mapped[int] = mapped_column(ForeignKey("quizquestions.id", ondelete="CASCADE"))
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(String(300), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # задел на будущее
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    question: Mapped["QuizQuestion"] = relationship("QuizQuestion", back_populates="answers")

    __table_args__ = (
        UniqueConstraint("question_id", "number", name="uq_quizanswer_question_number"),
    )

    def __str__(self):
        return f"QuizAnswer(id={self.id}, text={self.text}, is_correct={self.is_correct})"


class QuizResponse(Base, Mixin):
    """Ответ пользователя на вопрос."""

    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizs.id", ondelete="CASCADE"), index=True)
    user_uuid: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("quizquestions.id", ondelete="CASCADE"))
    answer_id: Mapped[int] = mapped_column(ForeignKey("quizanswers.id", ondelete="CASCADE"))
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    step: Mapped[int] = mapped_column(Integer, nullable=False)

    # задел на будущее
    attempt: Mapped[int] = mapped_column(Integer, default=1)

    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="responses")

    __table_args__ = (
        UniqueConstraint("user_uuid", "quiz_id", "step", name="uq_quizresponse_user_quiz_step"),
    )

    def __str__(self):
        return f"QuizResponse(user={self.user_uuid}, step={self.step}, correct={self.is_correct})"


class QuizUser(Base, Mixin):
    """Прохождение квиза пользователем."""

    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizs.id", ondelete="CASCADE"), index=True)
    user_uuid: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    end_quiz: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    step: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # задел на будущее
    attempts_used: Mapped[int] = mapped_column(Integer, default=0)
    best_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="users")

    __table_args__ = (
        UniqueConstraint("user_uuid", "quiz_id", name="uq_quizuser_user_quiz"),
    )

    def __str__(self):
        return f"QuizUser(user={self.user_uuid}, quiz_id={self.quiz_id}, step={self.step})"