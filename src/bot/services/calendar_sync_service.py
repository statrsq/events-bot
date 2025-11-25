import asyncio
from datetime import datetime, timezone
from typing import Any, Final
from loguru import logger

from src.bot.services.google_calendar import google_calendar_service
from src.bot.services.notification_service import NotificationService
from src.bot.db.models import Event
from src.bot.misc.enums.event_status import EventStatus
from src.bot.db.repositories.events import EventsRepository


class CalendarSyncService:
    def __init__(
        self, 
        notification_service: NotificationService, 
        sync_timeout: int = 60
    ):
        self.notification_service = notification_service
        self.sync_timeout = sync_timeout  # частота синхронизации
        self.event_repo = EventsRepository
        self.is_running = False

    async def start_sync(self):
        """Бесконечный фоновой цикл синхронизации."""
        if self.is_running:
            logger.warning("Синхронизация уже запущена")
            return

        self.is_running = True
        logger.info("Запуск фоновой синхронизации Google Calendar")

        while self.is_running:
            try:
                await self._sync_events()
            except Exception as e:
                logger.error(f"Ошибка синхронизации: {e}")

            await asyncio.sleep(self.sync_timeout)

    async def stop_sync(self):
        self.is_running = False
        logger.info("Остановка фоновой синхронизации")

    # MAIN SYNC
    async def _sync_events(self):
        """Основной метод: получает события, сверяет с БД, обрабатывает все изменения."""
        # Полученные события из Google Calendar
        google_events = await google_calendar_service.get_events()

        # События в базе
        google_event_ids: set[str] = {event["id"] for event in google_events}
        db_events = await self.event_repo.get_by_google_ids(google_event_ids)
        db_events_map = {
            event.google_event_id: event
            for event in db_events
        }

        # Сверяем
        for ge in google_events:
            ge_id = ge["id"]
            if ge_id in db_events_map:
                await self._update_event(db_events_map[ge_id], ge)
            else:
                await self._create_event(ge)

        await self.notification_service.send_reminders()

    # CREATE / UPDATE / DELETE
    async def _create_event(self, ge: dict[str, Any]) -> None:
        """Создание нового события."""
        start = self._parse_gcal_datetime(ge.get("start"))
        end = self._parse_gcal_datetime(ge.get("end"))

        description = ge.get("description", "")
        parsed_cfg = google_calendar_service.parse_event_description(description)

        event = await self.event_repo.create(
            google_event_id=ge["id"],
            title=ge.get("summary", "Без названия"),
            description=description,
            start_time=start,
            end_time=end,
            location=ge.get("location", ""),
            status=EventStatus.ACTIVE,
        )

        # если create() провалилось
        if not event:
            return

        # JSON-поля
        await self.event_repo.update(
            event,
            reminder_intervals=parsed_cfg.get("reminder_intervals", []),
            poll_interval=parsed_cfg.get("poll_interval", 24),
            deadline=self._parse_gcal_datetime(parsed_cfg.get("deadline"))
            if parsed_cfg.get("deadline")
            else None,
        )

        logger.info(f"Создано новое событие: {event.title}")
        await self.notification_service.notify_new_event(event)
        
    async def _cancel_event(self, local_event: Event):
        """Удалить событие из БД + отправить уведомление"""
        if local_event.status == EventStatus.CANCELLED:
            return

        await self.event_repo.update(local_event, status=EventStatus.CANCELLED)
        await self.notification_service.notify_event_cancelled(local_event)
        logger.info(f"Событие удалено из календаря: [{local_event.google_event_id}] {local_event.title}")

    async def _update_event(self, local_event: Event, google_event: dict[str, Any]):
        """Обновляет существующее событие, возвращает изменения."""
        update_data = {}

        if google_event.get("status") == "cancelled":
            await self._cancel_event(local_event)
            return

        # ------------ title ------------
        new_title = google_event.get("summary")
        if new_title and new_title != local_event.title:
            update_data["title"] = new_title

        # ------------ description ------------
        new_descr = google_event.get("description", "")
        if new_descr != local_event.description:
            update_data["description"] = new_descr

        # ------------ datetime ------------
        new_start = self._parse_gcal_datetime(google_event.get("start"))
        new_end = self._parse_gcal_datetime(google_event.get("end"))

        time_changed = False

        if new_start and new_start != local_event.start_time:
            update_data["start_time"] = new_start
            time_changed = True

        if new_end and new_end != local_event.end_time:
            update_data["end_time"] = new_end
            time_changed = True

        # ------------ location ------------
        new_loc = google_event.get("location", "")
        if new_loc != local_event.location:
            update_data["location"] = new_loc

        # ------------ JSON config ------------
        parsed_cfg = google_calendar_service.parse_event_description(
            google_event.get("description", "")
        )

        # update_data["reminder_intervals"] = parsed_cfg.get(
        #     "reminder_intervals", local_event.reminder_intervals
        # )
        # update_data["poll_interval"] = parsed_cfg.get(
        #     "poll_interval", local_event.poll_interval
        # )

        # if parsed_cfg.get("deadline"):
        #     update_data["deadline"] = self._parse_gcal_datetime(parsed_cfg["deadline"])

        # ------------ save if changed ------------
        if update_data:
            await self.event_repo.update(local_event, **update_data)

            if time_changed:
                logger.info(f"Событие перенесено: {local_event.title}")
                await self.notification_service.notify_event_postponed(local_event)
            else:
                logger.info(f"Событие обновлено: {local_event.title}")

    # DATETIME PARSING
    def _parse_gcal_datetime(self, obj: dict | str | None) -> datetime | None:
        """Google Calendar datetime parsing → UTC aware."""
        if not obj:
            return None

        try:
            # full object {"dateTime": "..."} OR {"date": "2025-01-01"}
            if isinstance(obj, dict):
                if "dateTime" in obj:
                    dt = obj["dateTime"]
                elif "date" in obj:
                    # All-day event
                    d = datetime.fromisoformat(obj["date"])
                    return d.replace(tzinfo=timezone.utc)
                else:
                    return None
            else:
                # deadline from JSON in description
                dt = obj

            # endswith Z → already UTC
            if dt.endswith("Z"):
                return datetime.fromisoformat(dt.replace("Z", "+00:00"))

            # other timezone → convert to UTC
            dt = datetime.fromisoformat(dt)
            return dt.astimezone(timezone.utc)

        except Exception as e:
            logger.error(f"Ошибка парсинга времени: {obj} -> {e}")
            return None


# SINGLETON
calendar_sync_service: Final[CalendarSyncService] = None

def get_or_create(
    notification_service: NotificationService,
    sync_timeout: int
) -> CalendarSyncService:
    global calendar_sync_service
    if calendar_sync_service is None:
        calendar_sync_service = CalendarSyncService(notification_service, sync_timeout)
    return calendar_sync_service

def get() -> CalendarSyncService | None:
    global calendar_sync_service
    return calendar_sync_service
