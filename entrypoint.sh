#!/bin/sh
# Выполняем миграции
echo "Running migrations..."
uv run aerich init-db
uv run aerich upgrade

# Запускаем бота (replace current process)
echo "Starting bot..."
exec uv run python -m src.bot.main.main