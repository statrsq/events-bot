# Events Bot

## Установка и настройка

### 1. Установка зависимостей
```bash
uv sync
```

### 2. Создание сервисного аккаунта + календаря
https://habr.com/ru/articles/525680/
1) Создаём сервисный аккаунт
2) Переходим в Google Calendar
* Открываем (или создаём новый) календарь
* Открываем настройки
* Shared with - добавляем email серсисного аккаунта
Права: see all event details


### 3. Настройка переменных окружения
Скопируйте `example.env` в `.env` и заполните необходимые переменные:

GOOGLE_CALENDAR_ID - из настроек Google-календаря: Integrate calendar -> Calendar ID


### 3. Запуск бота
* В терминале:
```bash
./entrypoint.sh
```

* Через докер:
```bash
docker compose up -d
```


## Структура проекта

```
src/
├── bot/
│   ├── db/                 # Модели базы данных
│   ├── handlers/           # Обработчики сообщений
│   │   ├── admin/          # Админские функции
│   │   ├── events/         # Обработка событий
│   │   └── user/           # Пользовательские функции
│   ├── services/           # Сервисы интеграции
│   ├── localization/       # Локализация
│   └── misc/              # Вспомогательные модули
```


## Разработка

### Добавление новых функций
1. Создайте обработчики в `src/bot/handlers/`
2. Добавьте модели в `src/bot/db/models/`
3. Обновите локализацию в `src/bot/localization/`
4. Создайте миграции для изменений БД


### Уведомления
Тексты:
src/bot/localization/locales/ru/text.ftl

Отправка уведомлений:
src/bot/services/notification_services.py


### Загрузка мероприятий
GoogleCalendarService - методы для работы с гугл календарём
CalendarSyncService - периодически синхронизирует с календарём

Видит мероприятия до +1 месяца от текущей даты
Изменить:
1) Указать time_max 
src/bot/services/calendar_sync_service.py
В методе CalendarSyncService.sync_events():
google_events = await google_calendar_service.get_events()
2) Изменить сервис календаря
src/bot/services/google_calendar.py
В методе GoogleCalendarService.get_events

### Количество пользователей на странице
src/bot/db/repositories/admin.py
AdminRepository.USERS_PER_PAGE

### Бан
Если пользователь в бане - не может заново отправить заявку
handlers/start.py
