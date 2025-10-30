import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any
from loguru import logger

from src.bot.services.google_calendar import google_calendar_service
from src.bot.services.notification_service import NotificationService
from src.bot.db.models import Event
from src.bot.misc.enums.event_status import EventStatus
from src.bot.db.repositories.events import EventsRepository


class CalendarSyncService:
    def __init__(self, bot):
        self.bot = bot
        self.notification_service = NotificationService(bot)
        self.event_repo = EventsRepository
        self.is_running = False
        self.sync_timeout = 30

    async def start_sync(self):
        """Запуск фоновой синхронизации с Google Calendar"""
        if self.is_running:
            logger.warning("Синхронизация уже запущена")
            return

        self.is_running = True
        logger.info("Запуск фоновой синхронизации с Google Calendar")

        while self.is_running:
            try:
                await self.sync_events()
            except Exception as e:
                logger.error(f"Ошибка синхронизации событий: {e}")
            await asyncio.sleep(self.sync_timeout)

    async def stop_sync(self):
        """Остановка фоновой синхронизации"""
        self.is_running = False
        logger.info("Остановка фоновой синхронизации")

    async def sync_events(self):
        """Синхронизация событий с Google Calendar"""
        try:
            # Получаем события из Google Calendar
            google_events = await google_calendar_service.get_events()

            # Получаем все активные события из БД для проверки отмен
            active_events = await self.event_repo.get_all_active()

            # Обрабатываем события
            await self.process_events(google_events, active_events)

            # Отправляем напоминания
            await self.notification_service.send_reminders()

        except Exception as e:
            logger.error(f"Ошибка синхронизации событий: {e}")

    async def process_events(self, google_events: list, active_events: list) -> None:
        """Обработка событий с проверкой отмен"""
        google_event_ids: set[str] = {google_event["id"] for google_event in google_events}
        existing_events = await self.event_repo.get_by_google_ids(google_event_ids)
        existing_events_map = {event.google_event_id: event for event in existing_events}

        # Проверяем отмененные события (есть в БД, но нет в Google Calendar)
        await self._check_cancelled_events(active_events, google_event_ids)

        # Обрабатываем существующие и новые события
        for google_event in google_events:
            google_event_id = google_event["id"]

            if google_event_id in existing_events_map:  # Событие уже существует - проверяем изменения
                await self._handle_existing_event(existing_events_map[google_event_id], google_event)
            else:  # Новое событие - создаем и уведомляем
                await self._handle_new_event(google_event)

    async def _check_cancelled_events(self, active_events: list, google_event_ids: set) -> None:
        """Проверяет события, которые были отменены (удалены из календаря)"""
        try:
            for event in active_events:
                if event.google_event_id not in google_event_ids:
                    # Событие есть в БД, но нет в Google Calendar - значит отменено
                    await self._cancel_event(event)
                    await self.notification_service.notify_event_cancelled(event)
                    logger.info(f"Событие отменено (удалено из календаря): {event.title}")

        except Exception as e:
            logger.error(f"Ошибка проверки отмененных событий: {e}")

    async def _handle_new_event(self, google_event: dict) -> None:
        """Обработка нового события"""
        try:
            event = await self._create_new_event(google_event)
            if event:
                logger.info(f"Обнаружено новое событие: {event.title}")
                await self.notification_service.notify_new_event(event)
        except Exception as e:
            logger.error(f"Ошибка обработки нового события: {e}")

    async def _handle_existing_event(self, event: Event, google_event: dict) -> None:
        """Обработка существующего события"""
        try:
            # Обновляем событие и проверяем тип изменений
            changes = await self._update_existing_event(event, google_event)

            # Логируем изменения для отладки
            if changes['any_changes']:
                logger.info(f"Обнаружены изменения в событии {event.title}: {changes}")

            # Проверяем изменения времени (перенос)
            if changes.get('time_changed'):
                await self.notification_service.notify_event_postponed(event)
                logger.info(f"Событие перенесено: {event.title}")

            elif changes.get('content_changed'):
                logger.info(f"Событие обновлено (контент): {event.title}")

        except Exception as e:
            logger.error(f"Ошибка обработки существующего события {event.id}: {e}")

    async def _create_new_event(self, google_event_data: dict[str, Any]) -> Event | None:
        """Создание нового события из данных Google Calendar"""
        try:
            start_time = self._parse_google_datetime(google_event_data['start'])
            end_time = self._parse_google_datetime(google_event_data['end'])

            logger.debug(f"Создание события: {google_event_data.get('summary')}")
            logger.debug(f"Start time raw: {google_event_data['start']}")
            logger.debug(f"Start time parsed: {start_time}")
            logger.debug(f"End time raw: {google_event_data['end']}")
            logger.debug(f"End time parsed: {end_time}")

            event = await self.event_repo.create(
                google_event_id=google_event_data['id'],
                title=google_event_data.get('summary', 'Без названия'),
                description=google_event_data.get('description', ''),
                start_time=start_time,
                end_time=end_time,
                location=google_event_data.get('location', ''),
                status=EventStatus.ACTIVE
            )

            if event:
                logger.info(f"Создано новое событие: {event.title}")

            return event

        except Exception as e:
            logger.error(f"Ошибка создания нового события: {e}")
            return None

    async def _update_existing_event(self, event: Event, google_event_data: dict[str, Any]) -> dict:
        """Обновление существующего события и возврат информации об изменениях"""
        try:
            update_data = {}
            changes = {
                'time_changed': False,
                'content_changed': False,
                'any_changes': False
            }

            # Проверяем изменения в названии
            new_title = google_event_data.get('summary', '')
            if new_title and new_title != event.title:
                update_data['title'] = new_title
                changes['content_changed'] = True

            # Проверяем изменения в описании
            new_description = google_event_data.get('description', '')
            if new_description != event.description:
                update_data['description'] = new_description
                changes['content_changed'] = True

            # Проверяем изменения во времени
            new_start = self._parse_google_datetime(google_event_data['start'])
            if new_start and new_start != event.start_time:
                update_data['start_time'] = new_start
                changes['time_changed'] = True

            new_end = self._parse_google_datetime(google_event_data['end'])
            if new_end and new_end != event.end_time:
                update_data['end_time'] = new_end
                changes['time_changed'] = True

            # Проверяем изменения в локации
            new_location = google_event_data.get('location', '')
            if new_location != event.location:
                update_data['location'] = new_location
                changes['content_changed'] = True

            if update_data:
                success = await self.event_repo.update(event, **update_data)
                changes['any_changes'] = success
                return changes

            return changes

        except Exception as e:
            logger.error(f"Ошибка обновления события {event.id}: {e}")
            return {'time_changed': False, 'content_changed': False, 'any_changes': False}

    async def _cancel_event(self, event: Event) -> bool:
        """Отмена события"""
        return await self.event_repo.update(event, status=EventStatus.CANCELLED)

    def _parse_google_datetime(self, datetime_dict: dict) -> datetime | None:
        """Парсинг datetime из Google Calendar API с конвертацией в UTC для базы данных"""
        try:
            if 'dateTime' in datetime_dict:
                dt_str = datetime_dict['dateTime']
                logger.debug(f"Парсим datetime: {dt_str}")

                if dt_str.endswith('Z'):
                    # UTC время - оставляем как есть
                    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                else:
                    # Время с явным часовым поясом - конвертируем в UTC
                    dt = datetime.fromisoformat(dt_str)
                    dt = dt.astimezone(timezone.utc)

                return dt

            elif 'date' in datetime_dict:
                # Для целых дней
                date_str = datetime_dict['date']
                dt = datetime.fromisoformat(date_str)
                # Для целых дней используем начало дня в UTC
                return dt.replace(tzinfo=timezone.utc)

            return None
        except Exception as e:
            logger.error(f"Ошибка парсинга datetime: {datetime_dict}, {e}")
            return None

    def _ensure_aware_datetime(self, dt: datetime) -> datetime:
        """Преобразует datetime в UTC для сохранения в базе"""
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            # Если часовой пояс не указан, считаем что это UTC
            return dt.replace(tzinfo=timezone.utc)
        # Конвертируем в UTC
        return dt.astimezone(timezone.utc)


# Глобальный экземпляр сервиса
calendar_sync_service = None


async def get_calendar_sync_service(bot):
    """Получение экземпляра сервиса синхронизации"""
    global calendar_sync_service
    if calendar_sync_service is None:
        calendar_sync_service = CalendarSyncService(bot)
    return calendar_sync_service