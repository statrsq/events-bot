from loguru import logger
from aiogram import Bot
from aiogram.types import Message

from src.bot.db.repositories.users import UsersRepository
from src.bot.localization.translator import LocalizedTranslator
from src.bot.db.models import User


class AdminActionLinks:
    """Утилита для создания текстовых ссылок действий администратора"""

    _ACTION_TEXTS = {
        "approve": "admin_action_approve",
        "reject": "admin_action_reject",
        "ban": "admin_action_ban",
        "unban": "admin_action_unban",
        "delete": "admin_action_delete",
        "details": "admin_action_details"
    }

    @staticmethod
    def create_action_url(bot_username: str, action: str, user_id: int) -> str:
        """Создает URL для действия администратора"""
        return f"https://t.me/{bot_username}?start={action}_{user_id}"

    @staticmethod
    def create_action_link(bot_username: str, action: str, user_id: int, translator: LocalizedTranslator) -> str:
        """Создает HTML ссылку для действия администратора"""
        text_key = AdminActionLinks._ACTION_TEXTS.get(action, action)
        text = translator.get(text_key)
        url = AdminActionLinks.create_action_url(bot_username, action, user_id)
        return f'<a href="{url}">{text}</a>'

    @staticmethod
    def create_back_link(bot_username: str, translator: LocalizedTranslator) -> str:
        """Создает ссылку для возврата в админ-панель"""
        text = translator.get("button_back")
        url = f"https://t.me/{bot_username}?start=admin"
        return f'<a href="{url}">⬅️ {text}</a>'

    @staticmethod
    def get_user_actions_text(bot_username: str, user_id: int, section: str, translator: LocalizedTranslator) -> str:
        """Генерирует текст с действиями для пользователя в зависимости от раздела"""
        actions_config = {
            "pending": ["approve", "reject", "ban"],
            "approved": ["ban", "details"],
            "banned": ["unban", "delete"]
        }

        actions = actions_config.get(section, [])
        links = [
            AdminActionLinks.create_action_link(bot_username, action, user_id, translator)
            for action in actions
        ]

        return " • ".join(links)

    @staticmethod
    def get_user_details_actions_text(bot_username: str, user_id: int, is_banned: bool,
                                      translator: LocalizedTranslator) -> str:
        """Генерирует текст с действиями для деталей пользователя"""
        main_action = "unban" if is_banned else "ban"
        links = [
            AdminActionLinks.create_action_link(bot_username, main_action, user_id, translator),
            AdminActionLinks.create_action_link(bot_username, "delete", user_id, translator),
            AdminActionLinks.create_back_link(bot_username, translator)
        ]

        return " • ".join(links)


class AdminActionHandler:
    """Обработчик административных действий"""

    _ACTION_HANDLERS = {
        "approve": "_handle_approve",
        "reject": "_handle_reject",
        "ban": "_handle_ban",
        "unban": "_handle_unban",
        "delete": "_handle_delete",
        "details": "_handle_details"
    }

    @staticmethod
    async def handle_action(action: str, target_user: User, message: Message,
                            translator: LocalizedTranslator) -> str | None:
        """Обрабатывает административное действие и возвращает текст результата"""
        handler_name = AdminActionHandler._ACTION_HANDLERS.get(action)
        if not handler_name:
            return f"❌ Неизвестное действие: {action}"

        handler = getattr(AdminActionHandler, handler_name)
        return await handler(target_user, message, translator)

    @staticmethod
    async def _handle_approve(user: User, message: Message, translator: LocalizedTranslator) -> str:
        await UsersRepository.approve_user(user)
        await AdminActionHandler._notify_user(message.bot, user.telegram_id, "user_approved_notification", translator)
        return translator.get("admin_action_completed_approve", name=user.name)

    @staticmethod
    async def _handle_reject(user: User, message: Message, translator: LocalizedTranslator) -> str:
        await UsersRepository.delete_user(user)
        return translator.get("admin_action_completed_reject", name=user.name)

    @staticmethod
    async def _handle_ban(user: User, message: Message, translator: LocalizedTranslator) -> str:
        await UsersRepository.ban_user(user)
        await AdminActionHandler._notify_user(message.bot, user.telegram_id, "user_banned_notification", translator)
        return translator.get("admin_action_completed_ban", name=user.name)

    @staticmethod
    async def _handle_unban(user: User, message: Message, translator: LocalizedTranslator) -> str:
        await UsersRepository.unban_user(user)
        await AdminActionHandler._notify_user(message.bot, user.telegram_id, "user_unbanned_notification", translator)
        return translator.get("admin_action_completed_unban", name=user.name)

    @staticmethod
    async def _handle_delete(user: User, message: Message, translator: LocalizedTranslator) -> str:
        await UsersRepository.delete_user(user)
        return translator.get("admin_action_completed_delete", name=user.name)

    @staticmethod
    async def _handle_details(user: User, message: Message, translator: LocalizedTranslator) -> None:
        """Обработка действия details - не возвращает текстовый результат"""
        return None

    @staticmethod
    async def _notify_user(bot: Bot, user_id: int, message_key: str, translator: LocalizedTranslator) -> None:
        """Отправляет уведомление пользователю"""
        try:
            await bot.send_message(user_id, translator.get(message_key))
        except Exception as e:
            logger.warning(f"Не удалось отправить уведомление пользователю {user_id}: {e}")