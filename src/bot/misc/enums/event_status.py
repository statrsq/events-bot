from enum import Enum


class EventStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    POSTPONED = "postponed"
    COMPLETED = "completed"
