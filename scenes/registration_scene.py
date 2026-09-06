import logging
from datetime import datetime

from database.users_crud import get_user_by_uuid, save_user_registration

import re
from typing import Optional

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import Scene, on
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardRemove
)

from keyboards.inline_keyboard import i_get_start_keyboard, i_get_cancel_keyboard, i_get_confirm_keyboard
from keyboards.reply_keyboar import r_get_phone_keyboard
from lexicon.constants import steps
from lexicon.lexicon import Lexicon

logger = logging.getLogger(__name__)
router = Router(name=__name__)


class RegistrationScene(Scene, state="registration_scene"):
    """Сцена регистрации студентов"""

    DEFAULT_LANG = "RU"

    # ============================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ============================================================
    # @staticmethod  # 👈 Добавляем декоратор
    # def parse_birth_date(date_str: str) -> Optional[datetime.date]:
    #     """
    #     Преобразует строку с датой в объект datetime
    #
    #     Args:
    #         date_str: Строка с датой (например: "01.01.2000", "01.01.2000)", "01.01.2000")
    #
    #     Returns:
    #         Optional[datetime]: Объект datetime или None
    #     """
    #     if not date_str:
    #         return None
    #
    #     # ✅ Очищаем от лишних символов
    #     cleaned = re.sub(r'[()\[\]{}\"\' \s]', '', date_str.strip())
    #
    #     if not cleaned:
    #         return None
    #
    #     # ✅ Проверяем формат и преобразуем
    #     try:
    #         return datetime.strptime(cleaned, "%d.%m.%Y").date()
    #     except ValueError:
    #         return None
    @classmethod
    def get_next_step(cls, current_step: str) -> str:
        """Определяет следующий шаг"""
        try:
            index = steps.index(current_step)
            return steps[index + 1] if index + 1 < len(steps) else "confirm"
        except (ValueError, IndexError):
            return "confirm"

    @classmethod
    def get_previous_step(cls, current_step: str) -> Optional[str]:
        """Определяет предыдущий шаг"""
        try:
            index = steps.index(current_step)
            return steps[index - 1] if index > 0 else None
        except (ValueError, IndexError):
            return None

    @classmethod
    async def save_to_database(cls, user_id: int, user_data: dict) -> None:
        """Сохранение данных в базу данных"""
        try:
            await save_user_registration(user_data=user_data, uuid=str(user_id))  # type: ignore
            logger.info(f"✅ Студент {user_id} успешно зарегистрирован")
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных: {e}")

    # ============================================================
    # ОТОБРАЖЕНИЕ ШАГА (ЕДИНСТВЕННОЕ МЕСТО ОТПРАВКИ СООБЩЕНИЙ)
    # ============================================================
    @classmethod
    async def normalize_phone(cls, phone: str) -> str:
        """
        Приводит телефон к формату +375XXXXXXXXX

        Поддерживает:
        - +375296261405
        - 375296261405
        - 296261405
        - +375 29 626-14-05
        - 8 029 626-14-05
        """
        # Удаляем все пробелы, дефисы, скобки
        phone = re.sub(r'[\s\-\(\)]', '', phone)

        # Если начинается с 8 — заменяем на +375
        if phone.startswith('8'):
            phone = '+375' + phone[1:]

        # Если начинается с 375 (без +) — добавляем +
        if phone.startswith('375') and not phone.startswith('+'):
            phone = '+' + phone

        # Если только 9 цифр — добавляем +375
        if re.match(r'^\d{9}$', phone):
            phone = '+375' + phone

        return phone

    async def process_phone_contact(self, message: Message, state: FSMContext):
        """Обработка контакта с телефоном"""
        data = await state.get_data()
        user_data = data.get("user_data", {})

        phone = message.contact.phone_number
        # if phone.startswith('8'):
        #     phone = '+7' + phone[1:]
        # elif not phone.startswith('+'):
        #     phone = '+7' + phone

        user_data["phone"] = phone
        next_step = self.get_next_step("phone")

        # ✅ Удаляем клавиатуру после получения контакта
        await message.answer(
            f"✅ Телефон получен: {phone}",
            reply_markup=ReplyKeyboardRemove()
        )

        await state.update_data(step=next_step, user_data=user_data)
        await self.show_step(message, state)

    async def show_step(self, message: Message, state: FSMContext):
        """
        Показывает сообщение для текущего шага.
        Единственное место, где отправляются сообщения!
        """
        data = await state.get_data()
        step = data.get("step", "start")
        user_data = data.get("user_data", {})

        logger.info(f"📢 show_step: {step}")

        # Завершение регистрации
        if step == "completed":
            await message.answer(
                "🎉 Регистрация успешно завершена!\n\n"
                "Теперь вы можете пользоваться всеми функциями бота.\n"
                "Используйте команды из меню.",
                reply_markup=ReplyKeyboardRemove()
            )
            # await state.clear()
            await self.wizard.exit()
            return

        # Отмена регистрации - ТОЛЬКО ЗАВЕРШАЕМ, НЕ ЗАПУСКАЕМ ЗАНОВО!
        if step == "cancelled":
            await message.answer(
                "❌ Регистрация отменена.\n\n"
                "Вы можете начать заново через команду /registration",
                reply_markup=ReplyKeyboardRemove()
            )
            await state.clear()
            await self.wizard.exit()
            # ✅ НЕ вызываем здесь новую регистрацию!
            return

        # Показываем сообщение в зависимости от шага
        match step:
            case "start":
                await message.answer(
                    "🎓 Добро пожаловать в систему регистрации!\n\n"
                    "Вы хотите пройти регистрацию?",
                    reply_markup=i_get_start_keyboard()
                )

            case "surname":
                await message.answer(
                    "👤 Введите вашу Фамилию:",
                    reply_markup=i_get_cancel_keyboard()
                )

            case "given_name":
                await message.answer(
                    "👤 Введите ваше Имя:",
                    reply_markup=i_get_cancel_keyboard()
                )

            case "middle_name":
                await message.answer(
                    "👤 Введите ваше Отчество:",
                    reply_markup=i_get_cancel_keyboard()
                )

            case "group":
                await message.answer(
                    "📚 Введите номер вашей группы (например: ИС-41):",
                    reply_markup=i_get_cancel_keyboard()
                )

            case "phone":
                await message.answer(
                    "📞 Введите ваш номер телефона в формате +375XXXXXXXXX\n"
                    "Или нажмите кнопку '📱 Отправить номер' ниже:",
                    reply_markup=r_get_phone_keyboard()
                )

            case "email":
                await message.answer(
                    "📧 Введите ваш Email (или напишите 'нет'):",
                    reply_markup=i_get_cancel_keyboard()
                )

            case "birth_date":
                await message.answer(
                    "📅 Введите вашу дату рождения (например: 01.01.2000):",
                    reply_markup=i_get_cancel_keyboard()
                )

            case "nationality":
                await message.answer(text=f"🌍 {Lexicon.get_text(lang="RU", key="nationality")}",
                                     reply_markup=i_get_cancel_keyboard()
                                     )

            case "term_time_address":
                await message.answer(
                    "🏠 Введите адрес места проживания в период учебы:",
                    reply_markup=i_get_cancel_keyboard()
                )

            case "parents_info":
                await message.answer(
                    text=Lexicon.get_text(lang="RU", key="parents_info"),
                    reply_markup=i_get_cancel_keyboard()
                )
            case "status_family":
                await message.answer(text=Lexicon.get_text(lang="RU", key="status_family"),
                                     reply_markup=i_get_cancel_keyboard()
                                     )
            case "children":
                await message.answer(text=Lexicon.get_text(lang="RU", key="children"),
                                     reply_markup=i_get_cancel_keyboard()
                                     )
            case "low_income_family":
                await message.answer(text=Lexicon.get_text(lang="RU", key="low_income_family"),
                                     reply_markup=i_get_cancel_keyboard()
                                     )
            case "disability":
                await message.answer(text=Lexicon.get_text(lang="RU", key="disability"),
                                     reply_markup=i_get_cancel_keyboard())
            case "brsm":
                await message.answer(text=Lexicon.get_text(lang="RU", key="brsm"),
                                     reply_markup=i_get_cancel_keyboard())
            case "cas":
                await message.answer(text=Lexicon.get_text(lang="RU", key="cas"),
                                     reply_markup=i_get_cancel_keyboard())

            case "confirm":
                await message.answer(
                    f"✅ Проверьте введенные данные:\n\n"
                    f"👤 Фамилия: {user_data.get('surname', '❌ Не указана')}\n"
                    f"👤 Имя: {user_data.get('given_name', '❌ Не указано')}\n"
                    f"👤 Отчество: {user_data.get('middle_name', '❌ Не указано')}\n"
                    f"📚 Группа: {user_data.get('group', '❌ Не указана')}\n"
                    f"📞 Телефон: {user_data.get('phone', '❌ Не указан')}\n"
                    f"📧 Email: {user_data.get('email', 'Не указан')}\n"
                    f"📅 Дата рождения: {user_data.get('birth_date', '❌ Не указана')}\n"
                    f"🌍 Гражданство: {user_data.get('nationality', '❌ Не указана')}\n"
                    f"🏠 Адрес: {user_data.get('term_time_address', '❌ Не указан')}\n"
                    f"👨‍👩‍👦 Родители: {user_data.get('parents_info', '❌ Не указаны')}\n\n"
                    "Все данные верны?",
                    reply_markup=i_get_confirm_keyboard()
                )

            case _:
                await message.answer(
                    "⚠️ Неизвестный шаг.",
                    reply_markup=i_get_cancel_keyboard()
                )

    # ============================================================
    # ВХОД В СЦЕНУ
    # ============================================================

    @on.message.enter()
    async def on_enter(self, message: Message, state: FSMContext):
        """Вход в сцену - показывает текущий шаг"""
        # Проверка: зарегистрирован ли пользователь
        user = await get_user_by_uuid(uuid=str(message.from_user.id))
        if user and user.registration:
            await message.answer(
                "✅ Вы уже зарегистрированы!",
                reply_markup=ReplyKeyboardRemove()
            )
            await self.wizard.exit()
            # await send_main_menu(message.bot, message.chat.id, str(message.from_user.id))
            return
        # 2️⃣ Закрываем любую активную сцену
        # try:
        #     # await scenes.close()  # ✅ Закрываем сцену
        # except Exception as e:
        #     logger.warning(f"Ошибка при закрытии сцены: {e}")

        # Показываем текущий шаг
        await self.show_step(message, state)

    # ============================================================
    # ВЫХОД ИЗ СЦЕНЫ
    # ============================================================

    @on.message.exit()
    async def on_exit(self, message: Message, state: FSMContext):
        """Выход из сцены - очищаем состояние"""
        await state.clear()
        logger.info(f"👋 Выход из сцены для {message.from_user.id}")

    # ============================================================
    # ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ
    # ============================================================

    @on.message()
    async def process_message(self, message: Message, state: FSMContext):
        """Обработка текстовых сообщений и контактов"""
        data = await state.get_data()
        step = data.get("step", "start")
        user_data = data.get("user_data", {})

        logger.info(f"💬 [message] step: {step}, text: {message.text}")

        # Обработка кнопок Reply-клавиатуры
        if message.text == "◀️ Назад":
            await self.go_back(message, state)
            return

        if message.text == "❌ Отмена":
            # ✅ Просто отменяем
            await message.answer(
                "❌ Регистрация отменена.",
                reply_markup=ReplyKeyboardRemove()
            )
            await state.clear()
            await self.wizard.exit()
            return

        # Обработка контакта
        if message.contact:
            await self.process_phone_contact(message, state)
            return

        # Валидация и сохранение данных
        next_step = self.get_next_step(step)

        match step:
            case "surname":
                user_data["surname"] = message.text.strip()

            case "given_name":
                user_data["given_name"] = message.text.strip()

            case "middle_name":
                user_data["middle_name"] = message.text.strip()

            case "group":
                user_data["group"] = message.text.strip().upper()

            case "phone":
                raw_phone = message.text.strip()
                phone = await self.normalize_phone(raw_phone)

                # Проверяем финальный формат
                if not re.match(r'^\+375\d{9}$', phone):
                    await message.answer(
                        "❌ Неверный формат телефона.\nПример: +375XXXXXXXXX или 375XXXXXXXXX",
                        reply_markup=r_get_phone_keyboard()
                    )
                    return
                user_data["phone"] = phone

                # ✅ Удаляем клавиатуру после ввода телефона
                await message.answer(
                    f"✅ Телефон сохранен: {phone}",
                    reply_markup=ReplyKeyboardRemove()
                )

            case "email":
                email = message.text.strip()
                if email.lower() != 'нет' and not re.match(
                        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email
                ):
                    await message.answer(
                        "❌ Неверный формат Email.\nПример: user@example.com\nИли напишите 'нет'",
                        reply_markup=i_get_cancel_keyboard()
                    )
                    return
                user_data["email"] = email if email.lower() != 'нет' else None

            case "birth_date":
                # # ✅ Проверяем дату
                # birth_date_obj = self.parse_birth_date(message.text)
                """
                    Проверяет, является ли строка корректной датой в формате ДД.ММ.ГГГГ
                    """
                date_str = message.text.strip()
                pattern = r"^\d{2}\.\d{2}\.\d{4}$"
                if not date_str or not re.match(pattern, date_str.strip()) or not datetime.strptime(date_str.strip(),
                                                                                                    "%d.%m.%Y"):
                    await message.answer(
                        "❌ Неверный формат даты рождения.\n"
                        "Используйте формат: ДД.ММ.ГГГГ (например: 01.01.2000)",
                        reply_markup=i_get_cancel_keyboard()
                    )
                    return
                else:
                    # ✅ Сохраняем ОЧИЩЕННУЮ дату
                    user_data["birth_date"] = date_str  # 👈 Сохраняем ОБРАБОТАННЫЕ данные
                    next_step = self.get_next_step(step)

                # # ✅ Проверяем формат
                # pattern = r"^\d{2}\.\d{2}\.\d{4}$"
                # if not re.match(pattern, date_str.strip()):
                #     return False
                #
                # # ✅ Проверяем, что дата существует
                # try:
                #     datetime.strptime(date_str.strip(), "%d.%m.%Y")
                #     return True
                # except ValueError:
                #     return False
                #
                # if  is None:
                #     await message.answer(
                #         "❌ Неверный формат даты рождения.\n"
                #         "Используйте формат: ДД.ММ.ГГГГ (например: 01.01.2000)",
                #         reply_markup=self.get_cancel_keyboard()
                #     )
                #     return

                # # ✅ Сохраняем ОЧИЩЕННУЮ дату
                # user_data["birth_date"] = birth_date_obj  # 👈 Сохраняем ОБРАБОТАННЫЕ данные
                # next_step = self.get_next_step(step)

            case "nationality":
                user_data["nationality"] = message.text.strip()

            case "term_time_address":
                user_data["term_time_address"] = message.text.strip()

            case "parents_info":
                user_data["parents_info"] = message.text.strip()

            case "status_family":
                user_data["status_family"] = message.text.strip()

            case "children":
                text = message.text.strip().upper()
                if text.startswith("Д"):
                    user_data["children"] = "ДА"
                elif text.startswith("Н"):
                    user_data["children"] = "НЕТ"
                else:
                    # user_data["children"] = ""
                    await message.answer(
                        "❌ Неверный формат, повторите снова,\nответ в формате (да или нет)",
                        reply_markup=i_get_cancel_keyboard()
                    )
                    return
            case "low_income_family":
                text = message.text.strip().upper()
                if text.startswith("Д"):
                    user_data["low_income_family"] = "ДА"
                elif text.startswith("Н"):
                    user_data["low_income_family"] = "НЕТ"
                else:
                    # user_data["children"] = ""
                    await message.answer(
                        "❌ Неверный формат, повторите снова,\nответ в формате (да или нет)",
                        reply_markup=i_get_cancel_keyboard()
                    )
                    return

            case "disability":
                text = message.text.strip().upper()
                if text.startswith("Д"):
                    user_data["disability"] = "ДА"
                elif text.startswith("Н"):
                    user_data["disability"] = "НЕТ"
                else:
                    # user_data["children"] = ""
                    await message.answer(
                        "❌ Неверный формат, повторите снова,\nответ в формате (да или нет)",
                        reply_markup=i_get_cancel_keyboard()
                    )
                    return

            case "brsm":
                text = message.text.strip().upper()
                if text.startswith("Д"):
                    user_data["brsm"] = "ДА"
                elif text.startswith("Н"):
                    user_data["brsm"] = "НЕТ"
                else:
                    # user_data["children"] = ""
                    await message.answer(
                        "❌ Неверный формат, повторите снова,\nответ в формате (да или нет)",
                        reply_markup=i_get_cancel_keyboard()
                    )
                    return

            case "cas":
                text = message.text.strip().upper()
                if text.startswith("Д"):
                    user_data["cas"] = "ДА"
                elif text.startswith("Н"):
                    user_data["cas"] = "НЕТ"
                else:
                    # user_data["children"] = ""
                    await message.answer(
                        "❌ Неверный формат, повторите снова,\nответ в формате (да или нет)",
                        reply_markup=i_get_cancel_keyboard()
                    )
                    return

            case _:
                await message.answer("⚠️ Неизвестный шаг.")
                return

        # Сохраняем данные и переходим к следующему шагу
        await state.update_data(step=next_step, user_data=user_data)
        await self.show_step(message, state)

    # ============================================================
    # КНОПКА "НАЗАД"
    # ============================================================

    async def go_back(self, message: Message, state: FSMContext):
        """Обработка кнопки 'Назад'"""
        data = await state.get_data()
        step = data.get("step", "start")
        user_data = data.get("user_data", {})

        prev_step = self.get_previous_step(step)

        if prev_step:
            # Удаляем данные текущего шага
            if step in user_data:
                del user_data[step]

            await state.update_data(step=prev_step, user_data=user_data)

            # ✅ При возврате на шаг phone - клавиатура покажется заново в show_step
            await self.show_step(message, state)
        else:
            await message.answer(
                "❌ Нельзя вернуться назад.",
                reply_markup=ReplyKeyboardRemove()
            )

    # ============================================================
    # ОБРАБОТКА INLINE-КНОПОК
    # ============================================================

    @on.callback_query()
    async def process_callback(self, callback: CallbackQuery, state: FSMContext):
        """Обработка нажатий на inline-кнопки"""
        await callback.answer()

        data = await state.get_data()
        step = data.get("step", "start")
        user_data = data.get("user_data", {})

        logger.info(f"🔔 [callback] {callback.data}")

        match callback.data:
            case "start_reg":
                await state.update_data(step="surname")
                await callback.message.edit_text(
                    "✅ Отлично! Начинаем регистрацию...",
                    reply_markup=None
                )
                await self.show_step(callback.message, state)

            case "cancel_reg" | "cancel_mid":
                # ✅ Просто отменяем, НЕ запускаем show_step
                await callback.message.edit_text(
                    "❌ Регистрация отменена.",
                    reply_markup=None
                )

                # ✅ Очищаем состояние и выходим
                await state.clear()
                await self.wizard.exit()

                # ✅ Отправляем сообщение и ВСЁ!
                await callback.message.answer(
                    "Вы можете начать заново через команду /registration",
                    reply_markup=ReplyKeyboardRemove()
                )
                return  # ✅ Выходим, чтобы не было лишних вызовов

            case "confirm_yes":
                # Сохраняем данные в БД
                await self.save_to_database(user_id=callback.from_user.id, user_data=user_data)

                await callback.message.edit_text(
                    "✅ Данные подтверждены!",
                    reply_markup=None
                )
                await state.update_data(step="completed")
                await self.show_step(callback.message, state)

            case "confirm_no":
                # ✅ Возвращаем на шаг surname для исправления
                await callback.message.edit_text(
                    "🔄 Давайте начнем заново.",
                    reply_markup=None
                )

                # ✅ Очищаем user_data, но оставляем шаг
                await state.update_data(
                    step="surname",
                    user_data={}  # 👈 Очищаем данные
                )
                await self.show_step(callback.message, state)

            case "back":
                prev_step = self.get_previous_step(step)

                if prev_step:
                    if step in user_data:
                        del user_data[step]

                    await state.update_data(step=prev_step, user_data=user_data)
                    await callback.message.edit_text(
                        "◀️ Возврат...",
                        reply_markup=None
                    )
                    await self.show_step(callback.message, state)
                else:
                    await callback.message.edit_text(
                        "❌ Нельзя вернуться назад.",
                        reply_markup=None
                    )

            case "send_phone":
                await callback.message.edit_text(
                    "📱 Используйте кнопку 'Отправить номер' внизу экрана.",
                    reply_markup=None
                )
                await self.show_step(callback.message, state)

# ============================================================
# РЕГИСТРАЦИЯ КОМАНДЫ
# ============================================================

# def get_router() -> Router:
#     """Возвращает роутер с командой /registration"""
#     router = Router(name="registration_router")
#     router.message.register(RegistrationScene.as_handler(), Command("registration"))
#     return router

# @router.message(Command("cancel"))
# async def cmd_cancel(message: Message, state: FSMContext):
#     current_state = await state.get_state()
#     if current_state == "registration_scene":
#         await state.clear()
#         # await message.answer("❌ Регистрация отменена.")
#     else:
#         await message.answer("ℹ️ Нет активной регистрации.")
