import logging
from datetime import datetime, date

from database.connection import connection, readonly
from database.dao.quiz_dao import (
    QuizDAO, QuizQuestionDAO, QuizAnswerDAO,
    QuizResponseDAO, QuizUserDAO,
)
from models import Quiz, QuizQuestion, QuizAnswer
from services.EnumQuizStatus import QuizStatus
from services.services import get_timestamp

logger = logging.getLogger(__name__)


class ValidationError(ValueError):
    """Ошибка валидации JSON квиза."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("\n".join(errors))


class QuizService:

    # ==================== Валидация ====================

    @staticmethod
    @readonly
    async def validate_full(
            session,
            data: dict,
            exclude_quiz_id: int | None = None,
    ) -> list[str]:
        """Полная валидация: JSON + пересечение дат."""
        errors = QuizService.validate_json(data)
        if errors:
            return errors

        try:
            start_date = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
            end_date = datetime.strptime(data["end_date"], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return errors

        conflict = await QuizService.check_date_conflict(
            session=session,
            start_date=start_date,
            end_date=end_date,
            exclude_quiz_id=exclude_quiz_id,
        )
        if conflict:
            errors.append(
                f"❌ Квиз пересекается с квизом ID={conflict.id} "
                f"({conflict.start_date:%d.%m.%Y}—{conflict.end_date:%d.%m.%Y})"
            )

        return errors

    @staticmethod
    def validate_json(data: dict) -> list[str]:
        """Валидирует JSON квиза. Возвращает список ошибок (пусто = ок)."""
        errors: list[str] = []

        if not isinstance(data, dict):
            return ["❌ JSON должен быть объектом"]

        # ===== Корень =====

        title = data.get("title")
        if not title or not isinstance(title, str) or not title.strip():
            errors.append("❌ Поле title обязательно")
        elif len(title) > 200:
            errors.append("❌ title длиннее 200 символов")

        description = data.get("description")
        if description is not None and not isinstance(description, str):
            errors.append("❌ description должен быть строкой")

        # Даты
        start_date_str = data.get("start_date")
        end_date_str = data.get("end_date")
        start_date = end_date = None

        if not start_date_str:
            errors.append("❌ Поле start_date обязательно")
        else:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                errors.append("❌ start_date: неверный формат (YYYY-MM-DD)")

        if not end_date_str:
            errors.append("❌ Поле end_date обязательно")
        else:
            try:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                errors.append("❌ end_date: неверный формат (YYYY-MM-DD)")

        if start_date and end_date and start_date > end_date:
            errors.append("❌ start_date не может быть позже end_date")

        # Булевы настройки
        for field in ("show_correct_after_answer", "show_result_to_user"):
            if field in data and not isinstance(data[field], bool):
                errors.append(f"❌ {field} должен быть bool")

        # ===== Вопросы =====

        questions = data.get("questions")
        if not questions or not isinstance(questions, list):
            errors.append("❌ Список questions пуст")
            return errors

        seen_question_numbers: set[int] = set()

        for idx, q in enumerate(questions, start=1):
            if not isinstance(q, dict):
                errors.append(f"❌ Вопрос #{idx}: должен быть объектом")
                continue

            q_num = q.get("number")
            if not isinstance(q_num, int):
                errors.append(f"❌ Вопрос #{idx}: number обязателен (int)")
                q_label = f"#{idx}"
            else:
                if q_num in seen_question_numbers:
                    errors.append(f"❌ Вопрос #{idx}: дубль номера вопроса {q_num}")
                seen_question_numbers.add(q_num)
                q_label = f"#{idx} (number={q_num})"

            q_text = q.get("text")
            if not q_text or not isinstance(q_text, str) or not q_text.strip():
                errors.append(f"❌ Вопрос {q_label}: text обязателен")
            elif len(q_text) > 500:
                errors.append(f"❌ Вопрос {q_label}: text длиннее 500 символов")

            q_comment = q.get("comment")
            if q_comment is not None and not isinstance(q_comment, str):
                errors.append(f"❌ Вопрос {q_label}: comment должен быть строкой")

            answers = q.get("answers")
            if not answers or not isinstance(answers, list):
                errors.append(f"❌ Вопрос {q_label}: answers должен быть списком (≥2)")
                continue

            if len(answers) < 2:
                errors.append(f"❌ Вопрос {q_label}: нужно минимум 2 ответа (найдено {len(answers)})")
                continue

            seen_answer_numbers: set[int] = set()
            correct_count = 0

            for a_idx, a in enumerate(answers, start=1):
                if not isinstance(a, dict):
                    errors.append(f"❌ Вопрос {q_label}: ответ #{a_idx} должен быть объектом")
                    continue

                a_num = a.get("number")
                if not isinstance(a_num, int):
                    errors.append(f"❌ Вопрос {q_label}: ответ #{a_idx} — number обязателен (int)")
                    a_label = f"#{a_idx}"
                else:
                    if a_num in seen_answer_numbers:
                        errors.append(f"❌ Вопрос {q_label}: дубль номера ответа {a_num}")
                    seen_answer_numbers.add(a_num)
                    a_label = f"#{a_idx} (number={a_num})"

                a_text = a.get("text")
                if not a_text or not isinstance(a_text, str) or not a_text.strip():
                    errors.append(f"❌ Вопрос {q_label}: ответ {a_label} — text обязателен")
                elif len(a_text) > 300:
                    errors.append(f"❌ Вопрос {q_label}: ответ {a_label} — text длиннее 300 символов")

                is_correct = a.get("is_correct")
                if not isinstance(is_correct, bool):
                    errors.append(f"❌ Вопрос {q_label}: ответ {a_label} — is_correct обязателен (bool)")
                elif is_correct:
                    correct_count += 1

            if correct_count == 0:
                errors.append(f"❌ Вопрос {q_label}: нужен ровно 1 правильный ответ (найдено 0)")
            elif correct_count > 1:
                errors.append(f"❌ Вопрос {q_label}: нужен ровно 1 правильный ответ (найдено {correct_count})")

        return errors

    # ==================== Загрузка ====================

    @staticmethod
    @connection
    async def load_from_json(
            session, data: dict, created_by: str,
    ) -> int:
        """Загружает квиз в БД (валидация — в validate_full, до вызова)."""
        # Даты (уже провалидированы)
        start_date = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
        end_date = datetime.strptime(data["end_date"], "%Y-%m-%d").date()

        # Создание квиза
        quiz = Quiz(
            uuid=get_timestamp(),
            title=data["title"].strip(),
            description=(data.get("description") or "").strip() or None,
            start_date=start_date,
            end_date=end_date,
            status=QuizStatus.DRAFT,
            show_correct_after_answer=data.get("show_correct_after_answer", True),
            show_result_to_user=data.get("show_result_to_user", True),
            created_by=created_by,
        )
        quiz = await QuizDAO.add(session=session, data=quiz)

        # Вопросы + ответы
        for q in data["questions"]:
            question = QuizQuestion(...)
            question = await QuizQuestionDAO.add(session=session, data=question)
            answers = [...]
            await QuizAnswerDAO.add_many(session=session, data=answers)

        logger.info("QuizService.load_from_json: quiz_id=%s, ...", quiz.id)
        return quiz.id

    # services/quiz_service.py

    @staticmethod
    @readonly
    async def check_date_conflict(
            session,
            start_date: date,
            end_date: date,
            exclude_quiz_id: int | None = None,
    ) -> Quiz | None:
        """Проверяет пересечение дат с активными/DRAFT квизами."""
        return await QuizDAO.get_conflicting(
            session=session,
            start_date=start_date,
            end_date=end_date,
            exclude_quiz_id=exclude_quiz_id,
        )

    @staticmethod
    @readonly
    async def get_recent(session, limit: int = 5) -> list[Quiz]:
        """Последние N квизов (для админки)."""
        return await QuizDAO.get_recent(session=session, limit=limit)

    @staticmethod
    @connection
    async def activate_quiz(session, quiz_id: int) -> None:
        """Активировать квиз (DRAFT → ACTIVE)."""
        await QuizDAO.set_status(
            session=session, quiz_id=quiz_id, status=QuizStatus.ACTIVE,
        )
        logger.info("QuizService.activate_quiz: quiz_id=%s → ACTIVE", quiz_id)

    @staticmethod
    @readonly
    async def get_quiz(session, quiz_id: int) -> Quiz | None:
        """Получить квиз с вопросами и ответами."""
        return await QuizDAO.get_with_questions(session=session, quiz_id=quiz_id)

    # ==================== Чтение (для будущего) ====================

    @staticmethod
    @readonly
    async def get_quiz(session, quiz_id: int) -> Quiz | None:
        """Получить квиз с вопросами и ответами (selectinload)."""
        return await QuizDAO.get_with_questions(session=session, quiz_id=quiz_id)

    @staticmethod
    @readonly
    async def get_active_quiz(session, now=None) -> Quiz | None:
        """Активный квиз на сейчас."""
        if now is None:
            now = datetime.now()
        return await QuizDAO.get_active_with_questions(session=session, now=now)
