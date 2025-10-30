from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.localization.translator import LocalizedTranslator
from src.bot.misc.callback_data.admin import (
    AdminMenuCallback,
    UserManagementCallback,
    AdminSection,
    UserSection
)
from src.bot.db.repositories.admin import AdminRepository


def get_user_management_keyboard(translator: LocalizedTranslator, stats: dict) -> InlineKeyboardMarkup:
    """Клавиатура управления пользователями"""
    builder = InlineKeyboardBuilder()

    builder.button(
        text=translator.get("button_pending_users", count=stats['pending_users']),
        callback_data=UserManagementCallback(section=UserSection.PENDING, page=1)
    )
    builder.button(
        text=translator.get("button_approved_users", count=stats['approved_users']),
        callback_data=UserManagementCallback(section=UserSection.APPROVED, page=1)
    )
    builder.button(
        text=translator.get("button_banned_users", count=stats['banned_users']),
        callback_data=UserManagementCallback(section=UserSection.BANNED, page=1)
    )
    builder.button(
        text=translator.get("button_back"),
        callback_data=AdminMenuCallback(action=AdminSection.MAIN_MENU)
    )

    builder.adjust(1)
    return builder.as_markup()


def get_users_list_keyboard(
        translator: LocalizedTranslator,
        section: UserSection,
        page: int = 1,
        total_users: int = 0
) -> InlineKeyboardMarkup:
    """Клавиатура списка пользователей с пагинацией"""
    builder = InlineKeyboardBuilder()

    # Пагинация (только если есть больше одной страницы)
    total_pages = max(1, (total_users + AdminRepository.USERS_PER_PAGE - 1) // AdminRepository.USERS_PER_PAGE)

    if total_pages > 1:
        # Кнопка "Назад"
        if page > 1:
            builder.button(
                text="⬅️",
                callback_data=UserManagementCallback(section=section, page=page - 1)
            )

        # Информация о странице
        builder.button(
            text=f"{page}/{total_pages}",
            callback_data="noop"
        )

        # Кнопка "Вперед"
        if page < total_pages:
            builder.button(
                text="➡️",
                callback_data=UserManagementCallback(section=section, page=page + 1)
            )

    # Основные кнопки
    builder.button(
        text=translator.get("button_back"),
        callback_data=AdminMenuCallback(action=AdminSection.USER_MANAGEMENT)
    )
    builder.button(
        text=translator.get("button_refresh"),
        callback_data=UserManagementCallback(section=section, page=page)
    )

    if total_pages >= 3:  # Если есть пагинация
        if page == 1 or page == total_pages:
            builder.adjust(2, 2)
        else:
            builder.adjust(3, 2)
    else:  # Если нет пагинации
        builder.adjust(2)

    return builder.as_markup()