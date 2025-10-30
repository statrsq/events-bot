from aiogram import Bot
from loguru import logger

from src.bot.db.models import User
from src.bot.misc.callback_data.admin import UserSection
from src.bot.db.repositories.users import UsersRepository
from src.bot.services.deeplink_service import DeeplinkService
from src.bot.localization.translator import LocalizedTranslator


class AdminNotificationService:
    """Сервис для уведомлений администраторов"""

    @staticmethod
    async def notify_about_new_user(user: User, bot: Bot, translator: LocalizedTranslator) -> None:
        """Уведомить администраторов о новом пользователе"""
        try:
            admins = await UsersRepository.get_all_admins()
            bot_username = (await bot.me()).username

            for admin in admins:
                try:
                    text = AdminNotificationService._generate_new_user_notification(
                        user, bot_username, translator
                    )
                    await bot.send_message(
                        chat_id=admin.telegram_id,
                        text=text,
                        parse_mode="HTML",
                        disable_web_page_preview=True
                    )
                except Exception as e:
                    logger.warning(f"Не удалось уведомить администратора {admin.telegram_id}: {e}")

        except Exception as e:
            logger.error(f"Ошибка уведомления администраторов: {e}")

    @staticmethod
    def _generate_new_user_notification(user: User, bot_username: str, translator: LocalizedTranslator) -> str:
        """Сгенерировать текст уведомления о новом пользователе"""
        name = DeeplinkService.get_user_link(name=user.name, telegram_id=user.telegram_id)
        username = f"@{user.username}" if user.username else translator.get("not_specified")

        text = translator.get("admin_new_user_request") + "\n\n"
        text += translator.get(
            "user_management_user_item",
            index="1",
            telegram_id=str(user.telegram_id),
            name=name,
            username=username,
            id=user.id
        )

        # Добавляем действия
        text += "\n\n"
        text += DeeplinkService.get_section_actions(bot_username, user.id, UserSection.PENDING, translator)

        return text
