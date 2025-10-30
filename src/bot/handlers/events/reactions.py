from loguru import logger
from aiogram import Router
from aiogram.types import CallbackQuery

from src.bot.db.models import Event, EventParticipant, User
from src.bot.misc.enums.event_reaction import EventReaction
from src.bot.misc.callback_data.user import EventReactionCD
from src.bot.localization.translator import LocalizedTranslator


router = Router(name="reaction_handlers")


@router.callback_query(EventReactionCD.filter())
async def handle_reaction_callback(
    callback: CallbackQuery,
    callback_data: EventReactionCD,
    translator: LocalizedTranslator
):
    """Обработка callback для реакций на события"""
    try:
        # Получаем событие и пользователя
        event = await Event.get_or_none(id=callback_data.event_id)
        user = await User.get_or_none(telegram_id=callback.from_user.id)
        
        if not event or not user:
            await callback.answer(translator.get("error_event_not_found"), show_alert=True)
            return
        
        # Проверяем, одобрен ли пользователь
        if not user.is_approved:
            await callback.answer(translator.get("error_user_not_approved"), show_alert=True)
            return
        
        # Проверяем дедлайн для выбора "Пойду"
        if (callback_data.reaction == EventReaction.GOING and 
            event.deadline and 
            event.deadline < callback.message.date):
            await callback.answer(translator.get("error_deadline_passed"), show_alert=True)
            return
        
        # Обновляем или создаем реакцию
        participation, created = await EventParticipant.get_or_create(
            event=event,
            user=user,
            defaults={'reaction': callback_data.reaction}
        )
        
        if not created:
            participation.reaction = callback_data.reaction
            participation.reacted_at = callback.message.date
            await participation.save()
        
        # Отправляем подтверждение
        reaction_text = {
            EventReaction.GOING: translator.get("reaction_going"),
            EventReaction.NOT_GOING: translator.get("reaction_not_going"),
            EventReaction.THINKING: translator.get("reaction_thinking")
        }
        
        await callback.answer(f"Вы выбрали: {reaction_text[callback_data.reaction]}")
        
        logger.info(f"Пользователь {user.name} выбрал реакцию {callback_data.reaction} для события {event.title}")
        
    except Exception as e:
        logger.error(f"Ошибка обработки реакции: {e}")
        await callback.answer(translator.get("error_processing_reaction"), show_alert=True)
