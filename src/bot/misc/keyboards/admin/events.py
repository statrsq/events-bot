from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.localization.translator import LocalizedTranslator
from src.bot.misc.callback_data.admin import AdminMenuCallback, AdminSection


def get_event_stats_keyboard(translator: LocalizedTranslator) -> InlineKeyboardMarkup:
    """Клавиатура статистики событий"""
    builder = InlineKeyboardBuilder()

    builder.button(
        text=translator.get("button_back"),
        callback_data=AdminMenuCallback(action=AdminSection.MAIN_MENU)
    )

    return builder.as_markup()
