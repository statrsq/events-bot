from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.localization.translator import LocalizedTranslator
from src.bot.misc.callback_data.user import EventReactionCD
from src.bot.misc.enums.event_reaction import EventReaction


# EVENTS
def get_event_reaction_keyboard(
        translator: LocalizedTranslator,
        event_id: int,
        selected_reaction: EventReaction = None
) -> InlineKeyboardMarkup:
    """Клавиатура для выбора реакции на событие"""
    """Клавиатура для выбора реакции на событие с выделением выбранной опции"""
    builder = InlineKeyboardBuilder()

    reactions = [
        (EventReaction.GOING, "reaction_going", "✅"),
        (EventReaction.NOT_GOING, "reaction_not_going", "❌"),
        (EventReaction.THINKING, "reaction_thinking", "🤔")
    ]

    for reaction, translation_key, emoji in reactions:
        text = translator.get(translation_key)

        # Выделяем выбранную опцию
        if reaction == selected_reaction:
            text = f"▶️ {text} ◀️"
        else:
            text = f"{emoji} {text}"

        builder.button(
            text=text,
            callback_data=EventReactionCD(event_id=event_id, reaction=reaction)
        )

    builder.adjust(1)
    return builder.as_markup()

