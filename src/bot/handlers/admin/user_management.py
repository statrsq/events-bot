from aiogram import Router, F
from aiogram.types import CallbackQuery
from loguru import logger

from src.bot.db.repositories.admin import AdminRepository
from src.bot.db.repositories.users import UsersRepository
from src.bot.localization.translator import LocalizedTranslator
from src.bot.misc.callback_data.admin import (
    AdminSection, UserAction,
    AdminMenuCallback, UserManagementCallback, UserActionCallback
)
from src.bot.misc.keyboards.admin.users_management import (
    get_user_management_keyboard
)
from src.bot.services.deeplink_service import DeeplinkService
from src.bot.utils.functions.users_management import show_users_section

router = Router(name="admin_user_management")


@router.callback_query(AdminMenuCallback.filter(F.action == AdminSection.USER_MANAGEMENT))
async def show_user_management_menu(callback: CallbackQuery, translator: LocalizedTranslator):
    """Показать меню управления пользователями"""
    try:
        stats = await AdminRepository.get_admin_stats()
        text = translator.get("user_management_title")
        keyboard = get_user_management_keyboard(translator, stats)

        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка отображения меню пользователей: {e}")
        await callback.answer(translator.get("error_user_management"), show_alert=True)


@router.callback_query(UserManagementCallback.filter())
async def handle_users_section_callback(
        callback: CallbackQuery,
        callback_data: UserManagementCallback,
        translator: LocalizedTranslator
):
    """Обработать callback раздела пользователей с пагинацией"""
    await show_users_section(callback, callback_data.section, callback_data.page, translator)


@router.callback_query(UserManagementCallback.filter())
async def handle_users_section_callback(
        callback: CallbackQuery,
        callback_data: UserManagementCallback,
        translator: LocalizedTranslator
):
    """Обработать callback раздела пользователей"""
    await show_users_section(callback, callback_data.section, translator)


@router.callback_query(UserActionCallback.filter(F.action == UserAction.DETAILS))
async def show_user_details_callback(
        callback: CallbackQuery,
        callback_data: UserActionCallback,
        translator: LocalizedTranslator
):
    """Показать детали пользователя через callback"""
    try:
        user = await UsersRepository.get_by_id(callback_data.user_id)
        if not user:
            await callback.answer(translator.get("error_user_not_found"), show_alert=True)
            return

        await _show_user_details(callback, user, translator)
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка отображения деталей пользователя: {e}")
        await callback.answer(translator.get("error_processing_request"), show_alert=True)


async def _show_user_details(callback, user, translator: LocalizedTranslator):
    """Показать детали пользователя (вспомогательная функция)"""
    status_map = {
        (False, False): translator.get("user_status_pending"),
        (True, False): translator.get("user_status_approved"),
        (True, True): translator.get("user_status_banned")
    }

    status = status_map.get((user.is_approved, user.is_banned), translator.get("unknown"))

    # Получаем bot_username в зависимости от типа callback
    if hasattr(callback, 'bot'):
        bot_username = (await callback.bot.me()).username
    else:
        bot_username = (await callback._bot.me()).username

    text = translator.get("user_details_title") + "\n\n"
    text += translator.get(
        "user_details_info",
        name=user.name,
        username=f"@{user.username}" if user.username else translator.get("not_specified"),
        telegram_id=user.telegram_id,
        status=status,
        created_at=user.created_at.strftime('%d.%m.%Y %H:%M')
    )

    # Добавляем действия
    text += "\n\n<b>Действия:</b>\n"
    text += DeeplinkService.get_details_actions(
        bot_username, user.id, user.is_banned, translator
    )

    if hasattr(callback, 'message'):
        await callback.message.edit_text(text, parse_mode="HTML")
    else:
        await callback.answer(text, parse_mode="HTML")