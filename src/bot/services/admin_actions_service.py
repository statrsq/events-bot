from aiogram import Bot
from loguru import logger
from aiogram.types import Message

from src.bot.db.repositories.event_participants import EventParticipantsRepository
from src.bot.misc.callback_data.admin import UserSection
from src.bot.db.repositories.users import UsersRepository
from src.bot.db.repositories.events import EventsRepository
from src.bot.misc.enums.event_reaction import EventReaction
from src.bot.services.deeplink_service import DeeplinkService
from src.bot.localization.translator import LocalizedTranslator, Translator
from src.bot.services.notification_service import NotificationService
from src.bot.misc.keyboards.user import get_event_reaction_keyboard
from src.bot.utils.functions.user import get_user_link_str


class AdminActionService:
    """Сервис для обработки административных действий"""

    @staticmethod
    async def handle_admin_deeplink(message: Message, args: str, translator: LocalizedTranslator) -> None:
        """Обработать административное действие через deep link"""
        action, entity_id = AdminActionService._parse_action_args(args)
        if not action or not entity_id:
            await message.answer("❌ Неверный формат команды")
            return

        # --- поддержка event_<id> ---
        if action == "event":
            await _handle_event_participants(entity_id, message.bot, message, translator)
            return

        # --- остальные стандартные действия (approve, reject, и т.п.) ---
        result_text, navigation_section = await AdminActionService.handle_deeplink_action(
            action, entity_id, message, translator
        )

        if result_text:
            await message.answer(result_text)

        if navigation_section:
            await AdminActionService._show_user_management_section(message, navigation_section, translator)

    @staticmethod
    async def handle_deeplink_action(
            action: str,
            user_id: int,
            message: Message,
            translator: LocalizedTranslator
    ) -> tuple[str | None, UserSection | None]:
        """Обрабатывает стандартные действия deeplink"""
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
        await show_users_section(message, section, page=1, translator=translator)

    @staticmethod
    def _parse_action_args(args: str) -> tuple[str | None, int | None]:
        """Парсить аргументы действия, например approve_123 или event_45"""
        parts = args.split('_')
        if len(parts) != 2:
            return None, None

        action, id_str = parts
        try:
            return action, int(id_str)
        except ValueError:
            return None, None


# ---------------------------------------------------------------
# Обработчики стандартных действий пользователей (approve, ban и т.д.)
# ---------------------------------------------------------------

async def _handle_approve(user, bot: Bot, translator: LocalizedTranslator) -> str:
    await UsersRepository.approve_user(user)
    await _send_user_notification(user, bot, translator.get("user_approved_notification"))
    name = DeeplinkService.get_user_link(name=user.name, telegram_id=user.telegram_id)

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
    await UsersRepository.delete_user(user)
    name = DeeplinkService.get_user_link(name=user.name, telegram_id=user.telegram_id)
    return translator.get("admin_action_completed_reject", name=name)


async def _handle_ban(user, bot: Bot, translator: LocalizedTranslator) -> str:
    await UsersRepository.ban_user(user)
    await _send_user_notification(user, bot, translator.get("user_banned_notification"))
    name = DeeplinkService.get_user_link(name=user.name, telegram_id=user.telegram_id)
    return translator.get("admin_action_completed_ban", name=name)


async def _handle_unban(user, bot: Bot, translator: LocalizedTranslator) -> str:
    await UsersRepository.unban_user(user)
    await _send_user_notification(user, bot, translator.get("user_unbanned_notification"))
    name = DeeplinkService.get_user_link(name=user.name, telegram_id=user.telegram_id)
    return translator.get("admin_action_completed_unban", name=name)


async def _handle_delete(user, bot: Bot, translator: LocalizedTranslator) -> str:
    await UsersRepository.delete_user(user)
    name = DeeplinkService.get_user_link(name=user.name, telegram_id=user.telegram_id)
    return translator.get("admin_action_completed_delete", name=name)


async def _handle_details(user, bot: Bot, translator: LocalizedTranslator) -> None:
    return None


async def _send_user_notification(user, bot: Bot, text: str) -> None:
    try:
        await bot.send_message(user.telegram_id, text)
    except Exception as e:
        logger.warning(f"Не удалось отправить уведомление пользователю {user.telegram_id}: {e}")


# ---------------------------------------------------------------
# Просмотр участников события
# ---------------------------------------------------------------
async def _handle_event_participants(event_id: int, bot: Bot, message: Message, translator: LocalizedTranslator) -> None:
    """Показать участников события по deeplink event_<id>"""
    try:
        event = await EventsRepository.get_by_id(event_id)
        if not event:
            await message.answer("❌ Событие не найдено")
            return

        going = await EventParticipantsRepository.get_participants_by_reactions(event, [EventReaction.GOING])
        not_going = await EventParticipantsRepository.get_participants_by_reactions(event, [EventReaction.NOT_GOING])
        thinking = await EventParticipantsRepository.get_participants_by_reactions(event, [EventReaction.THINKING])

        going_list = "\n ".join([get_user_link_str(u.user) for u in going]) if going else "-"
        not_going_list = "\n ".join([get_user_link_str(u.user) for u in not_going]) if not_going else "-"
        thinking_list = "\n ".join([get_user_link_str(u.user) for u in thinking]) if thinking else "-"

        text = (
            f"📅 <b>{event.title}</b>\n\n"
            f"✅ Пойдут:\n {going_list}\n\n"
            f"❌ Не пойдут:\n {not_going_list}\n\n"
            f"🤔 Думают:\n {thinking_list}"
        )

        await message.answer(text, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Ошибка получения участников события: {e}")
        await message.answer("⚠️ Ошибка при получении участников события.")


def _get_navigation_section(action: str, user) -> UserSection:
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
