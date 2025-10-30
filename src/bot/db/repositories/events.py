from loguru import logger

from src.bot.db.models import Event
from src.bot.misc.enums.event_status import EventStatus


class EventsRepository:

    @staticmethod
    async def get_by_id(event_id: int) -> Event | None:
        """Получение события по ID"""
        try:
            return await Event.get_or_none(id=event_id)
        except Exception as e:
            logger.error(f"Ошибка получения события по ID {event_id}: {e}")
            return None

    @staticmethod
    async def get_by_google_id(google_event_id: str) -> Event | None:
        """Получение события по Google Calendar ID"""
        try:
            return await Event.get_or_none(google_event_id=google_event_id)
        except Exception as e:
            logger.error(f"Ошибка получения события по Google ID {google_event_id}: {e}")
            return None

    @staticmethod
    async def get_by_google_ids(google_event_ids: set[str]) -> list[Event]:
        """Получение событий по списку Google Calendar ID"""
        try:
            return await Event.filter(google_event_id__in=list(google_event_ids)).all()
        except Exception as e:
            logger.error(f"Ошибка получения событий по Google IDs: {e}")
            return []

    @staticmethod
    async def create(
        google_event_id: str,
        title: str,
        description: str,
        start_time,
        end_time,
        location: str = "",
        status: EventStatus = EventStatus.ACTIVE
    ) -> Event | None:
        """Создание нового события в БД"""
        try:
            event = await Event.create(
                google_event_id=google_event_id,
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                location=location,
                status=status
            )
            logger.info(f"Создано новое событие в БД: {title}")
            return event
        except Exception as e:
            logger.error(f"Ошибка создания события в БД: {e}")
            return None

    @staticmethod
    async def update(event: Event, **kwargs) -> bool:
        """Обновление события в БД"""
        try:
            for key, value in kwargs.items():
                if hasattr(event, key) and value is not None:
                    setattr(event, key, value)
            
            await event.save()
            logger.info(f"Обновлено событие в БД: {event.title}")
            return True
        except Exception as e:
            logger.error(f"Ошибка обновления события {event.id} в БД: {e}")
            return False

    @staticmethod
    async def get_all_active() -> list[Event]:
        """Получение всех активных событий"""
        try:
            return await Event.filter(status=EventStatus.ACTIVE).all()
        except Exception as e:
            logger.error(f"Ошибка получения активных событий из БД: {e}")
            return []

    @staticmethod
    async def delete(event: Event) -> bool:
        """Удаление события из БД"""
        try:
            await event.delete()
            logger.info(f"Удалено событие из БД: {event.title}")
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления события {event.id} из БД: {e}")
            return False
            