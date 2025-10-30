from typing import Callable, Dict, Any, Awaitable, Union

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from loguru import logger

# from src.database.engine import get_async_session
# from src.database.repo.user import UsersRepository
from src.bot.localization.translator import Translator


class TranslatorMiddleware(BaseMiddleware):

    def __init__(self, root_locale: str):
        self.root_locale: str = root_locale

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Union[Message, CallbackQuery],
            data: Dict[str, Any]
    ):
        translator: Translator = data["translator"]

        # ВРЕМЕННО
        new_data = data.copy()
        new_data["translator"] = translator(language=self.root_locale)
        return await handler(event, new_data)

        async for session in get_async_session():
            try:
                # Получаем пользователя из БД
                user_repo = UsersRepository(session=session)
                user = await user_repo.get_user(telegram_id=event.from_user.id)

                # Определяем язык
                locale = user.language if user else self.root_locale

                # Создаем копию данных с обновленным переводчиком
                new_data = data.copy()
                new_data["translator"] = translator(language=locale)

                return await handler(event, new_data)

            except Exception as e:
                logger.error(f"Translation error: {e}")
                # В случае ошибки используем язык по умолчанию
                new_data = data.copy()
                new_data["translator"] = translator(language=self.root_locale)
                return await handler(event, new_data)
