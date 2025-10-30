from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Self, Final
from os import environ



@dataclass(frozen=True, slots=True)
class BotConfig:
    token: str
    root_locale: str = "ru"

    @classmethod
    def load_from_env(cls) -> Self:
        token: str = environ["BOT_TOKEN"]

        return cls(
            token=token,
        )


@dataclass(frozen=True, slots=True)
class GoogleCalendarConfig:
    credentials_file: str
    calendar_id: str

    @classmethod
    def load_from_env(cls) -> Self:
        return cls(
            credentials_file=environ["GOOGLE_CREDENTIALS_FILE"],
            calendar_id=environ["GOOGLE_CALENDAR_ID"],
        )


@dataclass(frozen=True, slots=True)
class PostgresqlConfig:
    user: str
    password: str
    host: str
    port: int
    database: str

    @property
    def connection_url(self) -> str:
        return f"postgres://{self.user}:{self.password}@{self.host}/{self.database}"

    @classmethod
    def load_from_env(cls) -> Self:
        return cls(
            user=environ["POSTGRES_USER"],
            password=environ["POSTGRES_PASSWORD"],
            host=environ["POSTGRES_HOST"],
            port=int(environ["POSTGRES_PORT"]),
            database=environ["POSTGRES_DATABASE"],
        )


@dataclass(frozen=True, slots=True)
class Config:
    bot: BotConfig
    postgresql: PostgresqlConfig
    google_calendar: GoogleCalendarConfig

    @classmethod
    def load_from_env(cls) -> Self:
        return cls(
            bot=BotConfig.load_from_env(),
            postgresql=PostgresqlConfig.load_from_env(),
            google_calendar=GoogleCalendarConfig.load_from_env(),
        )


load_dotenv()
config: Final[Config] = Config.load_from_env()
