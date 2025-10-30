from typing import Any, Union, Dict

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from src.bot.db.repositories.users import UsersRepository


class IsAdminFilter(BaseFilter):

    async def __call__(
            self, update: Union[Message, CallbackQuery], *args: Any, **kwargs: Any
    ) -> Union[bool, Dict[str, Any]]:
        user_id = update.from_user.id
        return await UsersRepository.is_admin(user_telegram_id=user_id)
