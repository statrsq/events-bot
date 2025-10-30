from src.bot.localization.translator import LocalizedTranslator
from src.bot.misc.callback_data.admin import UserSection


class DeeplinkService:
    """Сервис для работы с deep links"""

    @staticmethod
    def create_action_link(bot_username: str, action: str, user_id: int, translator: LocalizedTranslator) -> str:
        """Создать HTML ссылку для действия"""
        action_texts = {
            "approve": translator.get("admin_action_approve"),
            "reject": translator.get("admin_action_reject"),
            "ban": translator.get("admin_action_ban"),
            "unban": translator.get("admin_action_unban"),
            "delete": translator.get("admin_action_delete"),
            # "details": translator.get("admin_action_details")
        }

        text = action_texts.get(action, action)
        url = f"https://t.me/{bot_username}?start={action}_{user_id}"
        return f'<a href="{url}">{text}</a>'

    @staticmethod
    def get_section_actions(bot_username: str, user_id: int, section: UserSection,
                            translator: LocalizedTranslator) -> str:
        """Получить действия для раздела"""
        action_configs = {
            UserSection.PENDING: {
                "approve_link": "approve",
                "reject_link": "reject",
                "ban_link": "ban"
            },
            UserSection.APPROVED: {
                "ban_link": "ban",
                # "details_link": "details"
            },
            UserSection.BANNED: {
                "unban_link": "unban",
                "delete_link": "delete"
            }
        }

        config = action_configs.get(section, {})
        action_links = {
            key: DeeplinkService.create_action_link(bot_username, action, user_id, translator)
            for key, action in config.items()
        }

        return translator.get(f"admin_user_actions_{section.value}", **action_links)

    @staticmethod
    def get_details_actions(bot_username: str, user_id: int, is_banned: bool, translator: LocalizedTranslator) -> str:
        """Получить действия для детального просмотра"""
        if is_banned:
            action_links = {
                "unban_link": DeeplinkService.create_action_link(bot_username, "unban", user_id, translator),
                "delete_link": DeeplinkService.create_action_link(bot_username, "delete", user_id, translator)
            }
        else:
            action_links = {
                "ban_link": DeeplinkService.create_action_link(bot_username, "ban", user_id, translator),
                "delete_link": DeeplinkService.create_action_link(bot_username, "delete", user_id, translator)
            }

        return translator.get(
            "admin_user_actions_details",
            is_banned=is_banned,
            **action_links
        )

    @staticmethod
    def get_user_link(name: str, telegram_id: int) -> str:
        return f"<a href='tg://user?id={telegram_id}'>{name}</a>"