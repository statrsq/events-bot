from tortoise import Tortoise

from src.bot.main.config import config


async def init_db():
    await Tortoise.init(
        db_url=config.postgresql.connection_url,
        modules={"models": ["src.bot.db.models"]},
    )
    await Tortoise.generate_schemas()


async def close_db():
    await Tortoise.close_connections()
