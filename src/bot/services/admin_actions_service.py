from aiogram import Bot
from loguru import logger
from aiogram.types import Message

from src.bot.misc.callback_data.admin import UserSection
from src.bot.db.repositories.users import UsersRepository
from src.bot.db.repositories.events import EventsRepository
from src.bot.services.deeplink_service import DeeplinkService
from src.bot.localization.translator import LocalizedTranslator, Translator
from src.bot.services.notification_service import NotificationService
from src.bot.misc.keyboards.user import get_event_reaction_keyboard


class AdminActionService:
    """Сервис для обработки административных действий"""

    @staticmethod
    async def handle_admin_deeplink(message: Message, args: str, translator: LocalizedTranslator) -> None:
        """Обработать административное действие через deep link"""
        action, user_id = AdminActionService._parse_action_args(args)
        if not action or not user_id:
            await message.answer("❌ Неверный формат команды")
            return

        result_text, navigation_section = await AdminActionService.handle_deeplink_action(
            action, user_id, message, translator
        )

        # Показать результат действия
        if result_text:
            await message.answer(result_text)

        # Показать соответствующий раздел
        if navigation_section:
            await AdminActionService._show_user_management_section(message, navigation_section, translator)

    @staticmethod
    async def handle_deeplink_action(
            action: str,
            user_id: int,
            message: Message,
            translator: LocalizedTranslator
    ) -> tuple[str | None, UserSection | None]:
        """
        Обрабатывает действие из deep link
        Возвращает (текст результата, раздел для навигации)
        """
        try:
            target_user = await UsersRepository.get_by_id(user_id)
            if not target_user:
                return translator.get("error_user_not_found"), None

            handler = _ACTION_HANDLERS.get(action)
            if not handler:
                return f"❌ Неизвестное действие: {action}", None

            result_text = await handler(target_user, message.bot, translator)
            navigation_section = _get_navigation_section(action, target_user)

            return result_text, navigation_section

        except Exception as e:
            logger.error(f"Ошибка обработки административного действия: {e}")
            return translator.get("error_processing_request"), None

    @staticmethod
    async def _show_user_management_section(
            message: Message,
            section: UserSection,
            translator: LocalizedTranslator
    ) -> None:
        """Показать раздел управления пользователями"""
        from src.bot.handlers.admin.user_management import show_users_section

        # Показываем первую страницу для deep links
        await show_users_section(message, section, page=1, translator=translator)

    @staticmethod
    def _parse_action_args(args: str) -> tuple[str | None, int | None]:
        """Парсить аргументы действия"""
        parts = args.split('_')
        if len(parts) != 2:
            return None, None

        action, user_id_str = parts
        try:
            return action, int(user_id_str)
        except ValueError:
            return None, None


async def _handle_approve(user, bot: Bot, translator: LocalizedTranslator) -> str:
    """Обработать одобрение пользователя"""
    await UsersRepository.approve_user(user)
    await _send_user_notification(user, bot, translator.get("user_approved_notification"))
    name = DeeplinkService.get_user_link(name=user.name, telegram_id=user.telegram_id)

    # После одобрения — отправляем пользователю все активные (запланированные) мероприятия
    try:
        events = await EventsRepository.get_all_active()
        if events:
            notification_service = NotificationService(bot)
            user_translator = Translator(root_locale="ru")(language=user.locale)

            for event in events:
                text = notification_service._format_new_event_text(event, user_translator)
                if not text:
                    continue
                keyboard = get_event_reaction_keyboard(user_translator, event.id)
                await notification_service._send_single_message_with_retry(
                    chat_id=user.telegram_id,
                    text=text,
                    keyboard=keyboard,
                    delay=0.05,
                )
    except Exception as e:
        logger.warning(f"Не удалось отправить пользователю {user.telegram_id} список мероприятий: {e}")

    return translator.get("admin_action_completed_approve", name=name)


async def _handle_reject(user, bot: Bot, translator: LocalizedTranslator) -> str:
    """Обработать отклонение пользователя"""
    await UsersRepository.delete_user(user)
    name = DeeplinkService.get_user_link(name=user.name, telegram_id=user.telegram_id)
    return translator.get("admin_action_completed_reject", name=name)


async def _handle_ban(user, bot: Bot, translator: LocalizedTranslator) -> str:
    """Обработать бан пользователя"""
    await UsersRepository.ban_user(user)
    await _send_user_notification(user, bot, translator.get("user_banned_notification"))
    name = DeeplinkService.get_user_link(name=user.name, telegram_id=user.telegram_id)
    return translator.get("admin_action_completed_ban", name=name)


async def _handle_unban(user, bot: Bot, translator: LocalizedTranslator) -> str:
    """Обработать разбан пользователя"""
    await UsersRepository.unban_user(user)
    await _send_user_notification(user, bot, translator.get("user_unbanned_notification"))
    name = DeeplinkService.get_user_link(name=user.name, telegram_id=user.telegram_id)
    return translator.get("admin_action_completed_unban", name=name)


async def _handle_delete(user, bot: Bot, translator: LocalizedTranslator) -> str:
    """Обработать удаление пользователя"""
    await UsersRepository.delete_user(user)
    name = DeeplinkService.get_user_link(name=user.name, telegram_id=user.telegram_id)
    return translator.get("admin_action_completed_delete", name=name)


async def _handle_details(user, bot: Bot, translator: LocalizedTranslator) -> None:
    """Обработать просмотр деталей - без текстового результата"""
    return None


async def _send_user_notification(user, bot: Bot, text: str) -> None:
    """Отправить уведомление пользователю"""
    try:
        await bot.send_message(user.telegram_id, text)
    except Exception as e:
        logger.warning(f"Не удалось отправить уведомление пользователю {user.telegram_id}: {e}")


def _get_navigation_section(action: str, user) -> UserSection:
    """Определить раздел для навигации после действия"""
    navigation_map = {
        "approve": UserSection.PENDING,
        "reject": UserSection.PENDING,
        "ban": UserSection.APPROVED,
        "unban": UserSection.BANNED,
        "delete": UserSection.BANNED,
        "details": UserSection.APPROVED
    }
    return navigation_map.get(action, UserSection.APPROVED)


_ACTION_HANDLERS = {
    "approve": _handle_approve,
    "reject": _handle_reject,
    "ban": _handle_ban,
    "unban": _handle_unban,
    "delete": _handle_delete,
    "details": _handle_details
}
