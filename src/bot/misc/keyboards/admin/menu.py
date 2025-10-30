from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.localization.translator import LocalizedTranslator
from src.bot.misc.callback_data.admin import AdminMenuCallback, AdminSection


def get_admin_menu_keyboard(translator: LocalizedTranslator) -> InlineKeyboardMarkup:
    """Клавиатура главного меню администратора"""
    builder = InlineKeyboardBuilder()

    builder.button(
        text=translator.get("button_user_management"),
        callback_data=AdminMenuCallback(action=AdminSection.USER_MANAGEMENT)
    )
    builder.button(
        text=translator.get("button_event_stats"),
        callback_data=AdminMenuCallback(action=AdminSection.EVENT_STATS)
    )
    builder.button(
        text=translator.get("button_broadcast"),
        callback_data=AdminMenuCallback(action=AdminSection.BROADCAST)
    )

    builder.adjust(1)
    return builder.as_markup()


def get_back_only_keyboard(translator: LocalizedTranslator) -> InlineKeyboardMarkup:
    """Простая клавиатура с кнопкой 'Назад'"""
    builder = InlineKeyboardBuilder()

    builder.button(
        text=translator.get("button_back"),
        callback_data=AdminMenuCallback(action=AdminSection.MAIN_MENU)
    )

    return builder.as_markup()
