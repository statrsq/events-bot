from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.localization.translator import LocalizedTranslator
from src.bot.misc.callback_data.admin import (
    AdminMenuCallback,
    AdminSection,
    BroadcastCallback,
    BroadcastAction
)


def get_broadcast_menu_keyboard(translator: LocalizedTranslator) -> InlineKeyboardMarkup:
    """Клавиатура меню рассылки"""
    builder = InlineKeyboardBuilder()

    builder.button(
        text=translator.get("button_start_broadcast"),
        callback_data=BroadcastCallback(action=BroadcastAction.START)
    )
    builder.button(
        text=translator.get("button_back"),
        callback_data=AdminMenuCallback(action=AdminSection.MAIN_MENU)
    )

    builder.adjust(1)
    return builder.as_markup()


def get_broadcast_confirmation_keyboard(translator: LocalizedTranslator) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения рассылки"""
    builder = InlineKeyboardBuilder()

    builder.button(
        text=translator.get("button_confirm_broadcast"),
        callback_data=BroadcastCallback(action=BroadcastAction.CONFIRM)
    )
    builder.button(
        text=translator.get("button_cancel"),
        callback_data=BroadcastCallback(action=BroadcastAction.CANCEL)
    )

    builder.adjust(2)
    return builder.as_markup()