FROM python:3.13-alpine

WORKDIR /bot

COPY .python-version uv.lock pyproject.toml ./

RUN pip install --no-cache-dir uv && \
    uv sync --no-dev --no-cache

COPY . .

ENV PYTHONPATH=/bot

# Запуск
COPY entrypoint.sh /bot/entrypoint.sh
RUN chmod +x /bot/entrypoint.sh
ENTRYPOINT ["/bot/entrypoint.sh"]