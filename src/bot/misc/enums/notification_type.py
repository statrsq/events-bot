from enum import Enum


class NotificationType(str, Enum):
    NEW_EVENT = "new_event"
    CANCELLED = "cancelled"
    POSTPONED = "postponed"
    REMINDER = "reminder"
