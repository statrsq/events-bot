#!/bin/sh
# Выполняем миграции
echo "Running migrations..."
uv run aerich init-db
uv run aerich upgrade

# Запускаем бота
echo "Starting bot..."
uv run python -m src.bot.main.main
