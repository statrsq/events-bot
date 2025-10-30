import os

from fluent_compiler.bundle import FluentBundle
from fluentogram import TranslatorHub, FluentTranslator, TranslatorRunner

from src.bot.misc.enums import LocaleEnum


class Translator:
    t_hub: TranslatorHub

    def __init__(self, root_locale: str):
        locales_path: os.path = os.path.join(os.getcwd(), "src", "bot", "localization", "locales")

        # Маппинг языков (основной + резервные)
        locales_map = {locale: (locale,) for locale in LocaleEnum}

        # Создаем трансляторы для каждого найденного языка
        translators = [
            FluentTranslator(
                locale=locale,
                translator=FluentBundle.from_files(
                    locale=locale,
                    filenames=[
                        str(os.path.join(locales_path, locale, "text.ftl")),
                    ]
                )
            )
            for locale in LocaleEnum
        ]

        self.t_hub = TranslatorHub(
            locales_map=locales_map,
            translators=translators,
            root_locale=root_locale,
        )

    def __call__(self, language: str, *args, **kwargs):
        return LocalizedTranslator(translator=self.t_hub.get_translator_by_locale(locale=language))


class LocalizedTranslator:
    translator: TranslatorRunner

    def __init__(self, translator: TranslatorRunner):
        self.translator = translator

    def get(self, key: str, **kwargs):
        for k, v in kwargs.items():
            if v is None or v == "":
                kwargs[k] = "empty"
        return self.translator.get(key, **kwargs)
