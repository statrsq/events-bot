from aiogram.exceptions import TelegramBadRequest
from loguru import logger

from src.bot.db.repositories.admin import AdminRepository
from src.bot.localization.translator import LocalizedTranslator
from src.bot.misc.callback_data.admin import (
    UserSection
)
from src.bot.misc.keyboards.admin.users_management import (
    get_users_list_keyboard
)
from src.bot.services.deeplink_service import DeeplinkService


async def show_users_section(
        callback,
        section: UserSection,
        page: int = 1,
        translator: LocalizedTranslator = None
):
    """Показать раздел с пользователями с пагинацией"""
    try:
        # Получаем данные
        users, total_users, bot_username, message_obj, is_callback = await _get_section_data(
            callback, section, page
        )

        # Формируем текст
        text = await _build_section_text(users, total_users, section, page, bot_username, translator)

        # Формируем клавиатуру
        keyboard = get_users_list_keyboard(translator, section, page, total_users)

        # Отображаем результат
        await _display_section_result(message_obj, text, keyboard, is_callback, callback)

    except TelegramBadRequest:
        await _handle_telegram_bad_request(callback, is_callback)
    except Exception as e:
        await _handle_section_error(e, section, callback, is_callback, translator)


async def _get_section_data(callback, section: UserSection, page: int):
    """Получить данные для отображения раздела"""
    users = await AdminRepository.get_users_by_section(section.value, page=page)
    total_users = await AdminRepository.get_users_count_by_section(section.value)

    # Определяем тип объекта (CallbackQuery или Message)
    if hasattr(callback, 'message') and hasattr(callback, 'bot'):
        # Это CallbackQuery
        bot_username = (await callback.bot.me()).username
        message_obj = callback.message
        is_callback = True
    else:
        # Это Message (для deep links)
        bot_username = (await callback.bot.me()).username
        message_obj = callback
        is_callback = False

    return users, total_users, bot_username, message_obj, is_callback


async def _build_section_text(
        users: list,
        total_users: int,
        section: UserSection,
        page: int,
        bot_username: str,
        translator: LocalizedTranslator
) -> str:
    """Построить текст раздела с пользователями"""
    # Заголовок раздела с информацией о пагинации
    section_title = translator.get(
        key=f"user_management_{section.value}_title",
        count=total_users
    )

    text = f"{translator.get('user_management_title')}\n\n{section_title}\n"

    # Информация о странице
    start_user = (page - 1) * AdminRepository.USERS_PER_PAGE + 1
    end_user = min(page * AdminRepository.USERS_PER_PAGE, total_users)
    if total_users > 0:
        text += translator.get(
            "pagination_info",
            start=start_user,
            end=end_user,
            total=total_users
        ) + "\n\n"

    # Список пользователей
    if users:
        text += await _build_users_list(users, start_user, bot_username, section, translator)
    else:
        text += translator.get("user_management_empty")

    return text


async def _build_users_list(
        users: list,
        start_index: int,
        bot_username: str,
        section: UserSection,
        translator: LocalizedTranslator
) -> str:
    """Построить список пользователей с действиями"""
    users_text = ""

    for i, user in enumerate(users, start_index):
        name = DeeplinkService.get_user_link(name=user.name, telegram_id=user.telegram_id)
        username = f"@{user.username}" if user.username else translator.get("not_specified")

        user_line = translator.get(
            "user_management_user_item",
            index=str(i),
            telegram_id=str(user.telegram_id),
            name=name,
            username=username,
            id=user.id
        )

        # Добавляем действия
        user_line += "\n   " + DeeplinkService.get_section_actions(
            bot_username, user.id, section, translator
        )

        users_text += user_line + "\n\n"

    return users_text


async def _display_section_result(message_obj, text: str, keyboard, is_callback: bool, callback):
    """Отобразить результат раздела"""
    if is_callback:
        await message_obj.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
    else:
        # Для Message из deep links
        await message_obj.answer(text, reply_markup=keyboard, parse_mode="HTML")


async def _handle_telegram_bad_request(callback, is_callback: bool):
    """Обработать ошибку TelegramBadRequest"""
    if hasattr(callback, 'answer') and callable(callback.answer):
        await callback.answer()


async def _handle_section_error(
        error: Exception,
        section: UserSection,
        callback,
        is_callback: bool,
        translator: LocalizedTranslator
):
    """Обработать ошибку отображения раздела"""
    logger.error(f"Ошибка отображения раздела {section}: {error}")

    if is_callback and hasattr(callback, 'answer') and callable(callback.answer):
        await callback.answer(translator.get("error_user_management"), show_alert=True)
    else:
        # Для Message или если нет возможности показать alert
        error_text = translator.get("error_user_management")
        if hasattr(callback, 'answer'):
            await callback.answer(error_text)
        elif hasattr(callback, 'reply'):
            await callback.reply(error_text)