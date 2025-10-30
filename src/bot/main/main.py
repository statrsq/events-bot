import asyncio

from loguru import logger
from aiogram.enums import ParseMode
from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from src.bot.main.config import config
from src.bot.localization.translator import Translator
from src.bot.misc.middlewares.translator import TranslatorMiddleware
from src.bot.db.engine import init_db, close_db
from src.bot.handlers.start import (
    router as start_router,
)
from src.bot.handlers.events import event_router, reaction_router
from src.bot.handlers.admin.user_management import router as admin_user_management
from src.bot.handlers.admin.events import router as admin_events
from src.bot.handlers.admin.broadcast import router as admin_broadcast
from src.bot.handlers.admin.menu import router as admin_menu
from src.bot.services.calendar_sync_service import get_calendar_sync_service

properties: DefaultBotProperties = DefaultBotProperties(parse_mode=ParseMode.HTML)
bot: Bot = Bot(token=config.bot.token, default=properties)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)


def setup_handlers(dispatcher: Dispatcher) -> None:
    main_router = Router(name="main_router")

    # register translator middleware
    translator_middleware = TranslatorMiddleware(root_locale=config.bot.root_locale)
    main_router.message.outer_middleware(translator_middleware)
    main_router.callback_query.outer_middleware(translator_middleware)

    # register db session middleware
    # main_router.message.outer_middleware(DBSessionMiddleware())
    # main_router.callback_query.outer_middleware(DBSessionMiddleware())
    # main_router.channel_post.outer_middleware(DBSessionMiddleware())

    # User handlers router
    user_router: Router = Router(name="users")
    user_router.include_routers(
        start_router,
    )

    # Event handlers router
    event_handlers_router: Router = Router(name="event_handlers")
    event_handlers_router.include_routers(
        event_router,
        reaction_router,
    )

    # Admin handlers router
    admin_handlers_router: Router = Router(name="admin_handlers")
    admin_handlers_router.include_routers(
        admin_menu,
        admin_user_management,
        admin_events,
        admin_broadcast
    )

    # Register all routers
    main_router.include_routers(
        user_router,
        event_handlers_router,
        admin_handlers_router
    )

    # register main router
    dispatcher.include_router(main_router)


async def on_startup():
    # Регистрация хэндлеров
    setup_handlers(dp)

    # Регистрация моделей БД
    await init_db()

    # Запуск фоновой синхронизации с Google Calendar
    calendar_sync = await get_calendar_sync_service(bot)
    asyncio.create_task(calendar_sync.start_sync())

    logger.info("Бот запущен!")


async def on_shutdown():
    # Остановка фоновой синхронизации
    calendar_sync = await get_calendar_sync_service(bot)
    await calendar_sync.stop_sync()
    
    await close_db()
    logger.info("Бот остановлен!")


async def start_bot(bot: Bot, dispatcher: Dispatcher) -> None:
    dispatcher.startup.register(on_startup)
    dispatcher.shutdown.register(on_shutdown)
    await bot.delete_webhook(drop_pending_updates=False)

    try:
        # Запускаем поллинг
        await dispatcher.start_polling(
            bot,
            close_bot_session=True,
            translator=Translator(root_locale=config.bot.root_locale)
        )
    except Exception as e:
        logger.exception(e)


if __name__ == "__main__":
    asyncio.run(main=start_bot(bot=bot, dispatcher=dp))
