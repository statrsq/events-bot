from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest
from loguru import logger

from src.bot.db.models import Event
from src.bot.db.repositories.events import EventsRepository
from src.bot.db.repositories.users import UsersRepository
from src.bot.db.repositories.event_participants import EventParticipantsRepository
from src.bot.misc.enums.event_reaction import EventReaction
from src.bot.misc.callback_data.user import EventReactionCD
from src.bot.localization.translator import LocalizedTranslator
from src.bot.misc.keyboards.user import get_event_reaction_keyboard

router = Router(name="event_handlers")


@router.callback_query(EventReactionCD.filter())
async def handle_event_reaction(
        callback: CallbackQuery,
        callback_data: EventReactionCD,
        translator: LocalizedTranslator
):
    """Обработка реакции пользователя на событие"""
    try:
        # Получаем событие и пользователя через репозитории
        event = await EventsRepository.get_by_id(callback_data.event_id)
        user = await UsersRepository.get_by_telegram_id(callback.from_user.id)

        if not event or not user:
            await callback.answer(
                translator.get("error_event_not_found"),
                show_alert=True
            )
            return

        # Проверяем, одобрен ли пользователь
        if not user.is_approved:
            await callback.answer(
                translator.get("error_user_not_approved"),
                show_alert=True
            )
            return

        # Проверяем дедлайн для выбора "Пойду"
        if (callback_data.reaction == EventReaction.GOING and
                event.deadline and
                event.deadline < callback.message.date):
            await callback.answer(
                translator.get("error_deadline_passed"),
                show_alert=True
            )
            return

        # Обновляем реакцию пользователя
        await EventParticipantsRepository.get_or_create_participation(
            event=event,
            user=user,
            reaction=callback_data.reaction
        )

        # Обновляем клавиатуру
        current_reaction = await EventParticipantsRepository.get_user_reaction(event, user)
        await update_event_keyboard(callback, event, translator, current_reaction)

        text = translator.get(key="reaction_selected", reaction=callback_data.reaction)
        await callback.answer(text=text)
        logger.info(f"Пользователь {repr(user)} выбрал реакцию {callback_data.reaction} для события {repr(event)}")

    except Exception as e:
        logger.error(f"Ошибка обработки реакции на событие: {e}")
        # await callback.answer(
        #     translator.get("error_processing_reaction"),
        #     show_alert=True
        # )


async def update_event_keyboard(
        callback: CallbackQuery,
        event: Event,
        translator: LocalizedTranslator,
        current_reaction: EventReaction = None
):
    """Обновление клавиатуры события с выделением выбранной опции"""
    try:
        keyboard = get_event_reaction_keyboard(translator, event.id, current_reaction)
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except TelegramBadRequest:
        pass
    except Exception as e:
        logger.error(f"Ошибка обновления клавиатуры события: {e}")


async def create_event_notification(
        event: Event,
        translator: LocalizedTranslator
) -> tuple[str, InlineKeyboardMarkup]:
    """Создание уведомления о новом событии"""
    try:
        # Форматируем текст через Fluent
        text = translator.get(
            "event_new_notification",
            title=event.title,
            description=event.description or "",
            start_time=event.start_time.strftime('%d.%m.%Y %H:%M'),
            end_time=event.end_time.strftime('%d.%m.%Y %H:%M'),
            location=event.location,
            deadline=event.deadline.strftime('%d.%m.%Y %H:%M') if event.deadline else ""
        )

        # Создаем клавиатуру
        keyboard = get_event_reaction_keyboard(event.id, translator)

        return text, keyboard

    except Exception as e:
        logger.error(f"Ошибка создания уведомления о событии: {e}")
        return translator.get("error_event_notification_creation"), None
