from loguru import logger
from aiogram import Router, F
from aiogram.types import CallbackQuery

from src.bot.db.repositories.admin import AdminRepository
from src.bot.misc.callback_data.admin import AdminMenuCallback
from src.bot.localization.translator import LocalizedTranslator
from src.bot.misc.keyboards.admin.events import get_event_stats_keyboard
from src.bot.services.deeplink_service import DeeplinkService

router = Router(name="admin_events")


@router.callback_query(AdminMenuCallback.filter(F.action == "event_stats"))
async def event_statistics(callback: CallbackQuery, translator: LocalizedTranslator):
    """Статистика событий"""
    try:
        recent_events = await AdminRepository.get_recent_events()

        text = translator.get("event_stats_title") + "\n\n"
        bot_username: str = (await callback.bot.get_me()).username

        for event in recent_events:
            stats = await AdminRepository.get_event_stats(event)
            event_detail_link: str = DeeplinkService.get_event_details_link(
                bot_username=bot_username,
                event_id=event.id
            )
            event_title = f"<a href='{event_detail_link}'>{event.title}</a>"

            text += translator.get(
                "event_stats_item",
                title=event_title,
                going_count=stats['going_count'],
                not_going_count=stats['not_going_count'],
                thinking_count=stats['thinking_count']
            ) + "\n\n"

        keyboard = get_event_stats_keyboard(translator)
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка отображения статистики событий: {e}")
        await callback.answer(translator.get("error_event_stats"), show_alert=True)
