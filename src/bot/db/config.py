from src.bot.main.config import config

TORTOISE_ORM = {
    "connections": {"default": config.postgresql.connection_url},
    "apps": {
        "models": {
            "models": ["src.bot.db.models", "aerich.models"],
            "default_connection": "default",
        }
    },
}
