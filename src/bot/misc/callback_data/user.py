from aiogram.filters.callback_data import CallbackData
from src.bot.misc.enums.event_reaction import EventReaction


class UserMenuCD(CallbackData, prefix="user_menu"):
    action: str


class EventReactionCD(CallbackData, prefix="event_reaction"):
    event_id: int
    reaction: EventReaction
