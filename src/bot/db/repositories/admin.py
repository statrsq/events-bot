from loguru import logger
from src.bot.db.models import User, EventParticipant, Event
from src.bot.misc.enums.event_reaction import EventReaction


class AdminRepository:
    # Количество пользователей на странице
    USERS_PER_PAGE = 25

    @staticmethod
    async def get_admin_stats():
        """Получение статистики для админ-панели"""
        try:
            total_users = await User.all().count()
            approved_users = await User.filter(is_approved=True, is_banned=False).count()
            pending_users = await User.filter(is_approved=False, is_banned=False).count()
            banned_users = await User.filter(is_banned=True).count()

            return {
                'total_users': total_users,
                'approved_users': approved_users,
                'pending_users': pending_users,
                'banned_users': banned_users
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики админ-панели: {e}")
            return {
                'total_users': 0,
                'approved_users': 0,
                'pending_users': 0,
                'banned_users': 0
            }

    @staticmethod
    async def get_users_by_section(section: str, page: int = 1, limit: int = None):
        """Получение пользователей по разделу с пагинацией"""
        try:
            if limit is None:
                limit = AdminRepository.USERS_PER_PAGE

            offset = (page - 1) * limit

            if section == "pending":
                query = User.filter(is_approved=False, is_banned=False)
            elif section == "approved":
                query = User.filter(is_approved=True, is_banned=False)
            elif section == "banned":
                query = User.filter(is_banned=True)
            else:
                return []

            return await query.offset(offset).limit(limit).all()

        except Exception as e:
            logger.error(f"Ошибка получения пользователей по разделу {section}: {e}")
            return []

    @staticmethod
    async def get_users_count_by_section(section: str) -> int:
        """Получить общее количество пользователей в разделе"""
        try:
            if section == "pending":
                return await User.filter(is_approved=False, is_banned=False).count()
            elif section == "approved":
                return await User.filter(is_approved=True, is_banned=False).count()
            elif section == "banned":
                return await User.filter(is_banned=True).count()
            else:
                return 0
        except Exception as e:
            logger.error(f"Ошибка подсчета пользователей раздела {section}: {e}")
            return 0

    @staticmethod
    async def get_recent_events(limit: int = None):
        """Получение последних активных событий"""
        query = Event.filter(status="active").order_by('-created_at')
        if limit is not None:
            query = query.limit(limit=limit)
        return await query.all()

    @staticmethod
    async def get_event_stats(event):
        """Получение статистики реакций для события"""
        participants = await EventParticipant.filter(event=event).all()

        going_count = sum(1 for p in participants if p.reaction == EventReaction.GOING)
        not_going_count = sum(1 for p in participants if p.reaction == EventReaction.NOT_GOING)
        thinking_count = sum(1 for p in participants if p.reaction == EventReaction.THINKING)

        return {
            'going_count': going_count,
            'not_going_count': not_going_count,
            'thinking_count': thinking_count
        }
