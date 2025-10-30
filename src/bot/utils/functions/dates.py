from datetime import datetime, timezone, timedelta


def format_time(time: datetime, offset: int = 3) -> str:
    """Форматирование времени с конвертацией в указанный часовой пояс"""
    if time.tzinfo is None:
        # Если время без часового пояса, считаем что это UTC
        time = time.replace(tzinfo=timezone.utc)

    # Конвертируем в нужный часовой пояс
    target_tz = timezone(timedelta(hours=offset))
    local_time = time.astimezone(target_tz)
    return local_time.strftime('%d.%m.%Y %H:%M')