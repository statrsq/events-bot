from src.bot.db.models import EventNotification, Event
from src.bot.misc.enums.notification_type import NotificationType


class EventNotificationsRepository:
    @staticmethod
    async def create(event: Event, notification_type: NotificationType) -> EventNotification:
        result = await EventNotification.create(
            event=event,
            notification_type=notification_type,
        )
        return result

    @staticmethod
    async def get_last_reminder(event: Event) -> EventNotification | None:
        """Получение последнего напоминания для события"""
        return await EventNotification.filter(
            event=event,
            notification_type=NotificationType.REMINDER
        ).order_by('-sent_at').first()
