from enum import StrEnum


class LocaleEnum(StrEnum):
    # EN = "en"
    RU = "ru"

    @property
    def flag_emoji(self) -> str:
        """ Возвращает эмодзи с флагом для языка """
        emojis_map = {
            # LocaleEnum.EN: "🇺🇸",
            LocaleEnum.RU: "🇷🇺",
        }
        return emojis_map[self]

    @property
    def display_name(self) -> str:
        """ Возвращает название языка """
        names_map = {
            # LocaleEnum.EN: "English",
            LocaleEnum.RU: "Русский",
        }
        return names_map[self]

    @property
    def locale(self) -> str:
        names_map = {
            # LocaleEnum.EN: "en_US",
            LocaleEnum.RU: "ru_RU",
        }
        return names_map[self]
