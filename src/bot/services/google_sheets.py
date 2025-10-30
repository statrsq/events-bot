
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from loguru import logger

from src.bot.main.config import config
from src.bot.db.models import Event, EventParticipant
from src.bot.misc.enums.event_reaction import EventReaction


class GoogleSheetsService:
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    
    def __init__(self):
        self.service = None
        self.spreadsheet_id = config.google_calendar.sheets_id
        
    async def authenticate(self):
        """Аутентификация с Google Sheets API"""
        try:
            creds = None
            # Загружаем сохраненные учетные данные
            try:
                creds = Credentials.from_authorized_user_file('sheets_token.json', self.SCOPES)
            except FileNotFoundError:
                pass
            
            # Если нет действительных учетных данных, запрашиваем авторизацию
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        config.google_calendar.sheets_credentials_file, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Сохраняем учетные данные для следующего запуска
                with open('sheets_token.json', 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('sheets', 'v4', credentials=creds)
            logger.info("Успешная аутентификация с Google Sheets API")
            
        except Exception as e:
            logger.error(f"Ошибка аутентификации с Google Sheets API: {e}")
            raise
    
    async def export_event_statistics(self, event: Event) -> bool:
        """Экспорт статистики события в Google Sheets"""
        if not self.service:
            await self.authenticate()
        
        try:
            # Получаем всех участников события
            participants = await EventParticipant.filter(event=event).prefetch_related('user')
            
            # Группируем по реакциям
            going_users = []
            not_going_users = []
            thinking_users = []
            
            for participant in participants:
                user_info = f"@{participant.user.username}" if participant.user.username else participant.user.name
                
                if participant.reaction == EventReaction.GOING:
                    going_users.append(user_info)
                elif participant.reaction == EventReaction.NOT_GOING:
                    not_going_users.append(user_info)
                elif participant.reaction == EventReaction.THINKING:
                    thinking_users.append(user_info)
            
            # Подготавливаем данные для записи
            sheet_name = f"Событие_{event.id}_{event.title[:30]}"
            
            # Создаем лист для события
            await self._create_sheet(sheet_name)
            
            # Записываем статистику
            data = [
                ["Статистика события", event.title],
                ["Дата начала", event.start_time.strftime("%Y-%m-%d %H:%M")],
                ["Дата окончания", event.end_time.strftime("%Y-%m-%d %H:%M")],
                ["Место", event.location or "Не указано"],
                ["", ""],
                ["Пойдут", len(going_users)],
                ["Не пойдут", len(not_going_users)],
                ["Подумают", len(thinking_users)],
                ["", ""],
                ["Список участников:"],
                ["Пойдут:", ""],
            ]
            
            # Добавляем списки пользователей
            for user in going_users:
                data.append([user, ""])
            
            data.append(["Не пойдут:", ""])
            for user in not_going_users:
                data.append([user, ""])
            
            data.append(["Подумают:", ""])
            for user in thinking_users:
                data.append([user, ""])
            
            # Записываем данные в таблицу
            range_name = f"{sheet_name}!A1:B{len(data)}"
            body = {
                'values': data
            }
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            logger.info(f"Статистика события {event.title} экспортирована в Google Sheets")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка экспорта статистики в Google Sheets: {e}")
            return False
    
    async def _create_sheet(self, sheet_name: str):
        """Создание нового листа в таблице"""
        try:
            # Проверяем, существует ли лист
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            existing_sheets = [sheet['properties']['title'] for sheet in spreadsheet['sheets']]
            
            if sheet_name not in existing_sheets:
                # Создаем новый лист
                request_body = {
                    'requests': [{
                        'addSheet': {
                            'properties': {
                                'title': sheet_name
                            }
                        }
                    }]
                }
                
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body=request_body
                ).execute()
                
                logger.info(f"Создан новый лист: {sheet_name}")
            
        except Exception as e:
            logger.error(f"Ошибка создания листа {sheet_name}: {e}")
            raise


# Глобальный экземпляр сервиса
google_sheets_service = GoogleSheetsService()
