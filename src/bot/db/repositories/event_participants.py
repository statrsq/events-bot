from typing import Optional, Tuple
from loguru import logger

from src.bot.db.models import EventParticipant, Event, User
from src.bot.misc.enums.event_reaction import EventReaction


class EventParticipantsRepository:

    @staticmethod
    async def get_or_create_participation(
            event: Event,
            user: User,
            reaction: EventReaction
    ) -> Tuple[EventParticipant, bool]:
        """Получение или создание участия в событии"""
        try:
            participation, created = await EventParticipant.get_or_create(
                event=event,
                user=user,
                defaults={'reaction': reaction}
            )

            if not created:
                participation.reaction = reaction
                await participation.save()

            return participation, created

        except Exception as e:
            logger.error(f"Ошибка получения/создания участия: {e}")
            raise

    @staticmethod
    async def get_user_reaction(event: Event, user: User) -> EventReaction | None:
        """Получение реакции пользователя на событие"""
        try:
            participation = await EventParticipant.get_or_none(event=event, user=user)
            return participation.reaction if participation else None
        except Exception as e:
            logger.error(f"Ошибка получения реакции пользователя: {e}")
            return None

    @staticmethod
    async def get_participants_by_reactions(event, reactions: list):
        """Получение участников события по реакциям"""
        return await EventParticipant.filter(
            event=event,
            reaction__in=reactions
        ).prefetch_related('user').all()

    @staticmethod
    async def get_thinking_participants(event):
        """Получение участников, выбравших 'Подумаю'"""
        return await EventParticipant.filter(
            event=event,
            reaction=EventReaction.THINKING
        ).prefetch_related('user').all()
