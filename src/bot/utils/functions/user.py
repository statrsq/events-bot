from aiogram.types import User as TgUser

from src.bot.db.models import User
from src.bot.main.config import config
from src.bot.misc.enums.user_role import UserRole
from src.bot.db.repositories.users import UsersRepository


async def create_or_update_user(tg_user: TgUser) -> tuple[bool, User]:
    """ Создаёт пользователя """
    role = UserRole.USER
    if tg_user.id == config.bot.owner_id:
        role = UserRole.ADMIN

    is_created, user = await UsersRepository.create_or_update_user(
        telegram_id=tg_user.id,
        name=tg_user.full_name,
        username=tg_user.username,
        role=role
    )
    return is_created, user
