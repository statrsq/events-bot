import asyncio
from typing import Callable
from datetime import datetime

from loguru import logger
from aiogram.exceptions import TelegramRetryAfter

from src.bot.db.models import Event
from src.bot.localization.translator import Translator
from src.bot.db.repositories.users import UsersRepository
from src.bot.misc.enums.event_reaction import EventReaction
from src.bot.misc.enums.notification_type import NotificationType
from src.bot.misc.keyboards.user import get_event_reaction_keyboard
from src.bot.db.repositories.event_participants import EventParticipantsRepository
from src.bot.db.repositories.event_notifications import EventNotificationsRepository
from src.bot.utils.functions.dates import format_time


class NotificationService:
    def __init__(self, bot):
        self.bot = bot

    async def _send_single_message_with_retry(
            self,
            chat_id: int,
            text: str,
            keyboard: object | None = None,
            delay: float = 0.05
    ) -> bool:
        """
        Отправка одного сообщения
        """
        try:
            # Добавляем задержку между сообщениями
            if delay > 0:
                await asyncio.sleep(delay)

            message_kwargs = {"chat_id": chat_id, "text": text}
            if keyboard:
                message_kwargs["reply_markup"] = keyboard

            await self.bot.send_message(**message_kwargs)
            return True

        except TelegramRetryAfter as e:
            # Обработка ограничения частоты отправки
            retry_after = e.retry_after
            logger.warning(f"Rate limit exceeded for user {chat_id}. Retrying after {retry_after} seconds")
            await asyncio.sleep(retry_after)

            # Повторная попытка отправки
            try:
                await self.bot.send_message(**message_kwargs)
                return True
            except Exception as retry_error:
                logger.error(f"Failed to send message to user {chat_id} after retry: {retry_error}")
                return False

        except Exception as e:
            logger.warning(f"Failed to send message to user {chat_id}: {e}")
            return False

    async def _notify_users_with_personal_locale(
            self,
            users: list,
            event: Event,
            notification_type: NotificationType,
            text_formatter: Callable,
            keyboard_builder: Callable | None,
            log_message: str,
            delay_between_messages: float = 0.05
    ) -> None:
        """Базовый метод для отправки уведомлений с персональной локализацией"""
        sent_count = 0
        failed_count = 0

        await EventNotificationsRepository.create(event=event, notification_type=notification_type)

        for user in users:
            try:
                # Используем глобальную функцию для получения переводчика
                translator = Translator(root_locale="ru")(language=user.locale)

                text = text_formatter(translator)
                keyboard = keyboard_builder(translator) if keyboard_builder else None

                if not text:
                    logger.error(f"Пустой текст уведомления для пользователя {user.telegram_id}")
                    failed_count += 1
                    continue

                # Используем новый метод с обработкой retry и задержкой
                success = await self._send_single_message_with_retry(
                    chat_id=user.telegram_id,
                    text=text,
                    keyboard=keyboard,
                    delay=delay_between_messages
                )

                if success:
                    sent_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                logger.warning(f"Не удалось отправить уведомление пользователю {user.telegram_id}: {e}")
                failed_count += 1

        logger.info(f"Отправлено {sent_count} уведомлений о {log_message}. Не удалось: {failed_count}")

    async def _send_message_to_users_with_personal_locale(
            self,
            users: list,
            message_formatter: callable,
            delay_between_messages: float = 0.05
    ) -> int:
        """Отправка сообщения списку пользователей с персональной локализацией"""
        sent_count = 0
        failed_count = 0

        for user in users:
            try:
                translator = Translator(root_locale="ru")(language=user.locale)
                text = message_formatter(translator)

                # Используем новый метод с обработкой retry и задержкой
                success = await self._send_single_message_with_retry(
                    chat_id=user.telegram_id,
                    text=text,
                    delay=delay_between_messages
                )

                if success:
                    sent_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                logger.warning(f"Не удалось отправить сообщение пользователю {user.telegram_id}: {e}")
                failed_count += 1

        logger.info(f"Отправлено сообщений: {sent_count}, не удалось: {failed_count}")
        return sent_count

    # Старый метод оставляем для обратной совместимости, но помечаем как deprecated
    async def _send_single_message(
            self,
            chat_id: int,
            text: str,
            keyboard: object | None = None
    ) -> None:
        """Отправка одного сообщения (устаревший метод)"""
        logger.warning("Using deprecated _send_single_message method. Use _send_single_message_with_retry instead")
        await self._send_single_message_with_retry(chat_id, text, keyboard, delay=0)

    # Остальные методы класса остаются без изменений
    async def notify_new_event(self, event: Event) -> None:
        """Уведомление всех одобренных пользователей о новом событии"""
        users = await UsersRepository.get_approved_users()
        await self._notify_users_with_personal_locale(
            users=users,
            event=event,
            notification_type=NotificationType.NEW_EVENT,
            text_formatter=lambda translator: self._format_new_event_text(event, translator),
            keyboard_builder=lambda translator: get_event_reaction_keyboard(translator, event.id),
            log_message=f"новом событии: {event.title}"
        )

    async def notify_event_cancelled(self, event: Event) -> None:
        """Уведомление об отмене события"""
        participants = await EventParticipantsRepository.get_participants_by_reactions(
            event,
            [EventReaction.GOING, EventReaction.THINKING]
        )
        users = [participant.user for participant in participants]

        await self._notify_users_with_personal_locale(
            users=users,
            event=event,
            notification_type=NotificationType.CANCELLED,
            text_formatter=lambda translator: translator.get(
                "event_cancelled_notification",
                title=event.title,
                start_time=format_time(event.start_time)
            ),
            keyboard_builder=None,
            log_message=f"отмене события: {event.title}"
        )

    async def notify_event_postponed(self, event: Event) -> None:
        """Уведомление о переносе события"""
        participants = await EventParticipantsRepository.get_participants_by_reactions(
            event,
            [EventReaction.GOING, EventReaction.THINKING]
        )
        users = [participant.user for participant in participants]

        await self._notify_users_with_personal_locale(
            users=users,
            event=event,
            notification_type=NotificationType.POSTPONED,
            text_formatter=lambda translator: translator.get(
                "event_postponed_notification",
                title=event.title,
                start_time=format_time(event.start_time),
                location=event.location
            ),
            keyboard_builder=lambda translator: get_event_reaction_keyboard(translator, event.id),
            log_message=f"переносе события: {event.title}"
        )

    async def send_reminders(self) -> None:
        """Отправка напоминаний о событиях"""
        active_events = await Event.filter(status="active")

        for event in active_events:
            if not await self._should_send_reminder(event):
                continue

            await self._send_event_reminders(event)

    async def broadcast_message(self, message_text: str) -> int:
        """Отправка сообщения всем одобренным пользователям"""
        users = await UsersRepository.get_approved_users()
        return await self._send_message_to_users_with_personal_locale(
            users=users,
            message_formatter=lambda t: message_text,  # В рассылке текст одинаковый для всех
        )

    async def _send_event_reminders(self, event: Event) -> None:
        """Отправка напоминаний для конкретного события"""
        thinking_participants = await EventParticipantsRepository.get_thinking_participants(event)

        if not thinking_participants:
            return

        users = [participant.user for participant in thinking_participants]

        await self._notify_users_with_personal_locale(
            users=users,
            event=event,
            notification_type=NotificationType.REMINDER,
            text_formatter=lambda translator: translator.get(
                "event_reminder_notification",
                title=event.title,
                start_time=format_time(event.start_time),
                location=event.location
            ),
            keyboard_builder=lambda translator: get_event_reaction_keyboard(translator, event.id),
            log_message=f"напоминании для события: {event.title}"
        )

    async def _should_send_reminder(self, event: Event) -> bool:
        """Проверяет, нужно ли отправлять напоминание для события"""
        if not event.reminder_intervals:
            return False

        last_notification = await EventNotificationsRepository.get_last_reminder(event)

        if last_notification:
            time_since_last = datetime.now() - last_notification.sent_at
            if time_since_last.total_seconds() < event.poll_interval * 3600:
                return False

        return True

    def _format_new_event_text(self, event: Event, translator) -> str:
        """Форматирует текст для нового события"""
        try:
            data = {
                "title": event.title,
                "description": event.description or "",
                "start_time": format_time(event.start_time),
                "end_time": format_time(event.end_time),
                "location": event.location or "",
                "deadline": format_time(event.deadline) if event.deadline else ""
            }
            return translator.get("event_new_notification", **data)
        except Exception as e:
            logger.error(f"Ошибка форматирования текста события: {e}")
            return ""
 