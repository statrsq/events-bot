import json
from datetime import datetime, timedelta, timezone
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from loguru import logger

from src.bot.main.config import config
from src.bot.db.models import Event
from src.bot.misc.enums.event_status import EventStatus


class GoogleCalendarService:
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    
    def __init__(self, calendar_id: str, credentials_file: str):
        self.service = None
        self.calendar_id = calendar_id
        self.credentials_file = credentials_file
        
    async def authenticate(self):
        """Аутентификация с Google Calendar API"""
        try:
            # Загружаем учетные данные сервисного аккаунта
            creds = service_account.Credentials.from_service_account_file(
                filename=self.credentials_file,
                scopes=self.SCOPES
            )
            
            # Если указан email для делегирования прав
            if hasattr(config.google_calendar, 'delegated_user'):
                creds = creds.with_subject(config.google_calendar.delegated_user)
            
            self.service = build('calendar', 'v3', credentials=creds)
            logger.info("Успешная аутентификация через сервисный аккаунт Google Calendar API")
            
        except FileNotFoundError:
            logger.error(f"Файл сервисного аккаунта не найден: {self.credentials_file}")
            raise
        except Exception as e:
            logger.error(f"Ошибка аутентификации с Google Calendar API через сервисный аккаунт: {e}")
            raise
    
    async def get_events(self, time_min: datetime = None, time_max: datetime = None) -> list[dict[str, Any]]:
        """Получение событий из Google Calendar"""
        if not self.service:
            await self.authenticate()
        
        try:
            if not time_min:
                time_min = datetime.now(tz=timezone.utc)
            if not time_max:
                time_max = time_min + timedelta(days=30)
            
            # Форматируем даты в правильный формат для API
            time_min_str = time_min.isoformat().replace('+00:00', 'Z')
            time_max_str = time_max.isoformat().replace('+00:00', 'Z')
            
            logger.debug(f"Запрос событий с {time_min_str} по {time_max_str}")
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min_str,
                timeMax=time_max_str,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            logger.info(f"Получено {len(events)} событий из Google Calendar")
            return events
            
        except HttpError as e:
            logger.error(f"Ошибка получения событий из Google Calendar: {e}")
            raise
    
    async def get_event_by_id(self, event_id: str) -> dict[str, Any] | None:
        """Получение конкретного события по ID"""
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
        """Парсинг JSON-описания события"""
        try:
            if not description:
                return {}
            
            # Ищем JSON в описании
            import re
            json_match = re.search(r'\{.*\}', description, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            return {}
        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"Ошибка парсинга JSON из описания события: {e}")
            return {}
    
    async def sync_events(self) -> list[Event]:
        """Синхронизация событий с базой данных"""
        try:
            google_events = await self.get_events()
            synced_events = []
            
            for google_event in google_events:
                event_id = google_event.get('id')
                if not event_id:
                    continue
                
                # Проверяем, существует ли событие в БД
                existing_event = await Event.filter(google_event_id=event_id).first()
                
                # Парсим описание события
                description = google_event.get('description', '')
                parsed_config = self.parse_event_description(description)
                
                # Извлекаем данные события
                start_time = self._parse_datetime(google_event.get('start', {}))
                end_time = self._parse_datetime(google_event.get('end', {}))
                
                if not start_time or not end_time:
                    continue
                
                # Определяем статус события
                status = EventStatus.ACTIVE
                if google_event.get('status') == 'cancelled':
                    status = EventStatus.CANCELLED
                
                # Создаем или обновляем событие
                event_data = {
                    'google_event_id': event_id,
                    'title': google_event.get('summary', 'Без названия'),
                    'description': description,
                    'start_time': start_time,
                    'end_time': end_time,
                    'location': google_event.get('location'),
                    'status': status,
                    'reminder_intervals': parsed_config.get('reminder_intervals', []),
                    'poll_interval': parsed_config.get('poll_interval', 24),
                    'deadline': self._parse_datetime(parsed_config.get('deadline')) if parsed_config.get('deadline') else None
                }
                
                if existing_event:
                    for key, value in event_data.items():
                        setattr(existing_event, key, value)
                    await existing_event.save()
                    synced_events.append(existing_event)
                else:
                    new_event = await Event.create(**event_data)
                    synced_events.append(new_event)
                    logger.info(f"Создано новое событие: {new_event.title}")
            
            return synced_events
            
        except Exception as e:
            logger.error(f"Ошибка синхронизации событий: {e}")
            raise

    def _parse_datetime(self, datetime_obj: dict[str, Any]) -> datetime | None:
        """Парсинг даты и времени из Google Calendar API с правильным часовым поясом"""
        try:
            if 'dateTime' in datetime_obj:
                dt_str = datetime_obj['dateTime']
                logger.debug(f"Парсим datetime: {dt_str}")

                if dt_str.endswith('Z'):
                    # UTC время
                    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                else:
                    # Время с явным часовым поясом
                    dt = datetime.fromisoformat(dt_str)

                # Конвертируем в нужный часовой пояс (например, +3)
                from datetime import timezone, timedelta
                target_tz = timezone(timedelta(hours=3))
                return dt.astimezone(target_tz)

            elif 'date' in datetime_obj:
                # Для целых дней
                date_str = datetime_obj['date']
                dt = datetime.fromisoformat(date_str)
                # Для целых дней используем начало дня в нужном часовом поясе
                from datetime import timezone, timedelta
                target_tz = timezone(timedelta(hours=3))
                return dt.replace(tzinfo=target_tz)

            return None
        except (ValueError, KeyError) as e:
            logger.warning(f"Ошибка парсинга даты: {e}")
            return None


# Глобальный экземпляр сервиса
google_calendar_service = GoogleCalendarService(
    calendar_id=config.google_calendar.calendar_id,
    credentials_file=config.google_calendar.credentials_file
)
