from tortoise import Model, fields

from src.bot.misc.enums.event_reaction import EventReaction
from src.bot.misc.enums.event_status import EventStatus
from src.bot.misc.enums.notification_type import NotificationType


class Event(Model):
    id = fields.IntField(pk=True)
    google_event_id = fields.CharField(max_length=255, unique=True)
    title = fields.CharField(max_length=500)
    description = fields.TextField()
    start_time = fields.DatetimeField()
    end_time = fields.DatetimeField()
    location = fields.CharField(max_length=500, null=True)
    status = fields.CharEnumField(EventStatus, default=EventStatus.ACTIVE)
    
    # JSON поля для настроек события
    reminder_intervals = fields.JSONField(default=list)  # Интервалы напоминаний в минутах
    poll_interval = fields.IntField(default=24)  # Интервал повторного опроса в часах
    deadline = fields.DatetimeField(null=True)  # Дедлайн для выбора "Пойду"
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    def __str__(self):
        return self.title

    def __repr__(self):
        return f"[id:{self.id}] {self.title}"

    class Meta:
        table = "events"


class EventParticipant(Model):
    id = fields.IntField(pk=True)
    event = fields.ForeignKeyField("models.Event", related_name="participants")
    user = fields.ForeignKeyField("models.User", related_name="event_participations")
    reaction = fields.CharEnumField(enum_type=EventReaction, null=True)
    reacted_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "event_participants"
        unique_together = ("event", "user")


class EventNotification(Model):
    id = fields.IntField(pk=True)
    event = fields.ForeignKeyField("models.Event", related_name="notifications")
    notification_type = fields.CharEnumField(enum_type=NotificationType, null=False)
    sent_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "event_notifications"
