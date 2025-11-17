from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from tortoise.expressions import Q

from .service import Service
from ..models import Event
from ..config.settings import settings
from ..utils.exceptions import EventError, DatabaseError
from ..utils.helpers import is_owner, format_event_message
from ..utils.logger import setup_logger
from .user_settings_service import UserSettingsService

logger = setup_logger(__name__)


class EventService(Service):
    def __init__(self, user_settings_service: UserSettingsService):
        super().__init__(logger)
        self.user_settings_service = user_settings_service

    async def create_event(
        self,
        chat_id: int,
        user_id: int,
        event_data: Dict[str, Any],
        message_id: Optional[int] = None
    ) -> Event:
        try:
            owner_settings = await self.user_settings_service.get_owner_settings()

            reminder_times = event_data.get('reminder_times') or owner_settings.default_reminder_times

            if reminder_times and isinstance(reminder_times[0], str):
                from ..utils.helpers import parse_reminder_time
                reminder_times = [parse_reminder_time(time) for time in reminder_times]

            timezone = event_data.get('timezone') or owner_settings.timezone or settings.timezone

            event = await Event.create(
                chat_id=chat_id,
                message_id=message_id,
                creator_user_id=user_id,
                event_name=event_data['event_name'],
                description=event_data.get('description'),
                event_datetime=event_data['event_datetime'],
                end_datetime=event_data.get('end_datetime'),
                timezone=timezone,
                reminder_times=reminder_times or [],
                sent_reminders=[]
            )

            logger.info(f"Created event {event.id}: {event.event_name}")
            return event

        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            raise EventError(f"Could not create event: {e}")

    def generate_pinned_event_message(self, event: Event) -> str:
        #return format_pinned_event_message(
        return format_event_message(
            event_name=event.event_name,
            description=event.description,
            event_datetime=event.event_datetime,
            end_datetime=event.end_datetime,
            timezone=event.timezone
        )

    async def get_user_events(self, user_id: int, active_only: bool = True) -> List[Event]:
        """Get all events for a user."""
        try:
            query = Event.filter(creator_user_id=user_id)

            if active_only:
                query = query.filter(is_completed=False, is_cancelled=False)

            return await query.order_by('event_datetime').all()

        except Exception as e:
            logger.error(f"Failed to get events for user {user_id}: {e}")
            raise DatabaseError(f"Could not retrieve events: {e}")
