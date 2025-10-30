from loguru import logger

from src.bot.db.models import User
from src.bot.misc.enums.user_role import UserRole


class UsersRepository:

    @staticmethod
    async def create_or_update_user(
            telegram_id: int,
            name: str,
            username: str = None,
            role: UserRole = UserRole.USER,
    ) -> tuple[bool, User]:
        """ Создаёт или обновляет пользователя """
        defaults = {
            "name": name,
            "username": username,
            "role": role,
        }

        try:
            user, is_created = await User.update_or_create(
                telegram_id=telegram_id,
                defaults=defaults,
            )
        except Exception as e:
            logger.error(
                "Failed to create or update user. "
                f"telegram_id: {telegram_id}, "
                f"username: {username}, "
                f"error: {str(e)}"
            )
            raise

        return is_created, user

    @staticmethod
    async def get_by_telegram_id(telegram_id: int) -> User | None:
        """Получение пользователя по Telegram ID"""
        try:
            return await User.get_or_none(telegram_id=telegram_id)
        except Exception as e:
            logger.error(f"Ошибка получения пользователя по Telegram ID {telegram_id}: {e}")
            return None

    @staticmethod
    async def get_approved_users():
        """Получение всех одобренных пользователей"""
        return await User.filter(is_approved=True, is_banned=False).all()

    @staticmethod
    async def get_by_id(user_id: int):
        """Получение пользователя по ID"""
        return await User.get_or_none(id=user_id)

    @staticmethod
    async def approve_user(user):
        """Одобрение пользователя"""
        user.is_approved = True
        await user.save()

    @staticmethod
    async def delete_user(user):
        """Удаление пользователя"""
        await user.delete()

    @staticmethod
    async def ban_user(user):
        user.is_banned = True
        await user.save()

    @staticmethod
    async def unban_user(user):
        user.is_banned = False
        await user.save()

    @staticmethod
    async def get_all_admins():
        """Получение всех администраторов"""
        return await User.filter(role=UserRole.ADMIN).all()

    @staticmethod
    async def is_admin(user_telegram_id: int) -> bool:
        """Проверяет, является ли пользователь администратором"""
        try:
            user = await User.get_or_none(telegram_id=user_telegram_id)
            return user and user.role == UserRole.ADMIN
        except Exception as e:
            logger.error(f"Ошибка проверки прав администратора для {user_telegram_id}: {e}")
            return False
