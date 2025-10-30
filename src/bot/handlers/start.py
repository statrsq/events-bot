from loguru import logger
from aiogram import Router
from aiogram.types import Message, User as TgUser
from aiogram.filters import CommandStart, CommandObject

from src.bot.db.repositories.users import UsersRepository
from src.bot.services.admin_actions_service import AdminActionService
from src.bot.utils.functions.user import create_or_update_user
from src.bot.localization.translator import LocalizedTranslator
from src.bot.services.admin_notification_service import AdminNotificationService


router = Router(name="user_start")


@router.message(CommandStart())
async def handle_start(
        message: Message,
        command: CommandObject,
        translator: LocalizedTranslator,
) -> None:
    """Обработка команды /start"""
    tg_user = message.from_user

    # Обработка административных действий
    if command.args and await UsersRepository.is_admin(tg_user.id):
        await AdminActionService.handle_admin_deeplink(message, command.args, translator)
        return

    # Обработка обычного пользователя
    await _handle_user_start(message, tg_user, translator)


async def _handle_user_start(message: Message, tg_user: TgUser, translator: LocalizedTranslator) -> None:
    """Обработать старт для обычного пользователя"""
    is_created, user = await create_or_update_user(tg_user)

    if is_created:
        await AdminNotificationService.notify_about_new_user(user, message.bot, translator)
        await message.answer(text=translator.get("start_welcome"))
        logger.info(f"Новый пользователь {user.name} ({user.telegram_id})")
        return

    # Существующий пользователь
    if user.is_banned:
        await message.answer(text=translator.get("start_banned"))
    elif user.is_approved:
        await message.answer(text=translator.get("start_welcome_back"))
    else:
        await message.answer(text=translator.get("start_pending"))
