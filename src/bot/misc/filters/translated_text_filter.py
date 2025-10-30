from collections.abc import Sequence
from typing import Any, Union, Dict

from aiogram.filters import BaseFilter
from aiogram.types import Message

from src.bot.localization.translator import LocalizedTranslator


class TranslatedTextFilter(BaseFilter):

    def __init__(self, text_key: str):
        self.key = text_key

    async def __call__(
            self, message: Message, *args: Any, **kwargs: Any
    ) -> Union[bool, Dict[str, Any]]:

        translator: LocalizedTranslator = kwargs.get("translator")

        if translator.get(self.key) == message.html_text:
            return True

        return False


class AnyTranslatedTextFilter(BaseFilter):

    def __init__(self, text_keys: Sequence[str]):
        self.keys = text_keys

    async def __call__(
            self, message: Message, *args: Any, **kwargs: Any
    ) -> Union[bool, Dict[str, Any]]:

        translator: LocalizedTranslator = kwargs.get("translator")

        for key in self.keys:
            if translator.get(key) == message.html_text:
                return True

        return False
