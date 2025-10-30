from enum import Enum


class EventReaction(str, Enum):
    GOING = "going"
    NOT_GOING = "not_going"
    THINKING = "thinking"
