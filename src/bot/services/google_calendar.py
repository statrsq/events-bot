import json
from datetime import datetime, timedelta, timezone
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from loguru import logger

from src.bot.main.config import config


class GoogleCalendarService:
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    
    def __init__(self, calendar_id: str, credentials_file: str):
        self.service = None
        self.calendar_id = calendar_id
        self.credentials_file = credentials_file
        
    async def authenticate(self):
        """Аутентификация с Google Calendar API"""
        try:
            creds = service_account.Credentials.from_service_account_file(
                filename=self.credentials_file,
                scopes=self.SCOPES
            )
            
            if hasattr(config.google_calendar, 'delegated_user'):
                creds = creds.with_subject(config.google_calendar.delegated_user)
            
            self.service = build('calendar', 'v3', credentials=creds)
            logger.info("Успешная аутентификация Google Calendar API")
            
        except FileNotFoundError:
            logger.error(f"Файл сервисного аккаунта не найден: {self.credentials_file}")
            raise
        except Exception as e:
            logger.error(f"Ошибка аутентификации Google Calendar API: {e}")
            raise
    
    async def get_events(self, time_min: datetime = None, time_max: datetime = None) -> list[dict[str, Any]]:

        if not self.service:
            await self.authenticate()
        
        try:
            if not time_min:
                time_min = datetime.now(tz=timezone.utc)
            if not time_max:
                time_max = time_min + timedelta(days=30)

            time_min_str = time_min.isoformat().replace('+00:00', 'Z')
            time_max_str = time_max.isoformat().replace('+00:00', 'Z')
            
            logger.info(f"Запрос событий: {time_min_str} → {time_max_str}")
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min_str,
                timeMax=time_max_str,
                singleEvents=True,
                orderBy='startTime',
                showDeleted=True
            ).execute()

            events = events_result.get('items', [])
            logger.info(f"Получено событий: {len(events)}")
            return events
            
        except HttpError as e:
            logger.error(f"Ошибка получения событий: {e}")
            raise

    async def get_event_by_id(self, event_id: str) -> dict[str, Any] | None:
        """Получение конкретного события из Google Calendar"""
        if not self.service:
            await self.authenticate()
        
        try:
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            return event
        except HttpError as e:
            logger.error(f"Ошибка получения события {event_id}: {e}")
            return None
    
    def parse_event_description(self, description: str) -> dict[str, Any]:
        """Парсинг JSON внутри описания события"""
        try:
            if not description:
                return {}
            
            import re
            json_match = re.search(r'\{.*\}', description, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)

            return {}

        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"Ошибка парсинга JSON описания: {e}")
            return {}

    def parse_datetime(self, datetime_obj: dict[str, Any]) -> datetime | None:
        """
        Парсинг datetime из Google Calendar API.
        """
        try:
            if "dateTime" in datetime_obj:
                dt_str = datetime_obj["dateTime"]

                if dt_str.endswith("Z"):
                    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                else:
                    return datetime.fromisoformat(dt_str)

            elif "date" in datetime_obj:
                # date без времени — начало дня с таймзоной UTC
                date_str = datetime_obj["date"]
                return datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)

            return None

        except Exception as e:
            logger.warning(f"Ошибка парсинга даты {datetime_obj}: {e}")
            return None


# Глобальный экземпляр
google_calendar_service = GoogleCalendarService(
    calendar_id=config.google_calendar.calendar_id,
    credentials_file=config.google_calendar.credentials_file
)
