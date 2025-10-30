from aiogram.filters.callback_data import CallbackData
from enum import Enum


class AdminSection(str, Enum):
    """Разделы админ-панели"""
    MAIN_MENU = "main_menu"
    USER_MANAGEMENT = "user_management"
    EVENT_STATS = "event_stats"
    BROADCAST = "broadcast"


class UserSection(str, Enum):
    """Разделы управления пользователями"""
    PENDING = "pending"
    APPROVED = "approved"
    BANNED = "banned"


class UserAction(str, Enum):
    """Действия с пользователями"""
    APPROVE = "approve"
    REJECT = "reject"
    BAN = "ban"
    UNBAN = "unban"
    DELETE = "delete"
    DETAILS = "details"
    CANCEL = "cancel"


class AdminMenuCallback(CallbackData, prefix="admin"):
    action: AdminSection


class UserManagementCallback(CallbackData, prefix="user_mgmt"):
    section: UserSection
    page: int = 1


class UserActionCallback(CallbackData, prefix="user_action"):
    user_id: int
    action: UserAction


class BroadcastAction(str, Enum):
    START = "start"
    CONFIRM = "confirm"
    CANCEL = "cancel"


class BroadcastCallback(CallbackData, prefix="broadcast"):
    action: BroadcastAction
    