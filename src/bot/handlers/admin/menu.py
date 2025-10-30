from loguru import logger
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.exceptions import AiogramError
from aiogram.types import CallbackQuery, Message

from src.bot.misc.filters.is_admin import IsAdminFilter
from src.bot.db.repositories.admin import AdminRepository
from src.bot.misc.callback_data.admin import AdminMenuCallback
from src.bot.localization.translator import LocalizedTranslator
from src.bot.misc.keyboards.admin.menu import get_admin_menu_keyboard


router = Router(name="admin_menu")


@router.message(Command("admin"), IsAdminFilter())
async def admin_menu(message: Message, translator: LocalizedTranslator):
    """Главное меню администратора"""
    try:
        stats = await AdminRepository.get_admin_stats()

        text = translator.get("admin_menu_title") + "\n\n"
        text += translator.get("admin_stats_total_users", count=stats['total_users']) + "\n"
        text += translator.get("admin_stats_approved_users", count=stats['approved_users']) + "\n"
        text += translator.get("admin_stats_pending_users", count=stats['pending_users'])

        keyboard = get_admin_menu_keyboard(translator)
        await message.answer(text, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Ошибка отображения админского меню: {e}")
        await message.answer(translator.get("error_admin_menu"))


@router.callback_query(AdminMenuCallback.filter(F.action == "main_menu"))
async def admin_menu_callback(callback: CallbackQuery, translator: LocalizedTranslator):
    """Главное меню администратора (callback версия)"""
    await admin_menu(callback.message, translator)
    await callback.answer()
    try:
        await callback.message.delete()
    except AiogramError:
        pass
