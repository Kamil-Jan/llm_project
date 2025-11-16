import re
from datetime import datetime, timedelta
from typing import Optional, List
import pytz

from ..config.settings import settings
from .logger import setup_logger

logger = setup_logger(__name__)


def is_owner(user_id: int) -> bool:
    return user_id == settings.owner_user_id


def extract_chat_info(chat) -> tuple[int, str, str]:
    """Extract chat information from Telegram chat object."""
    chat_id = chat.id
    chat_title = getattr(chat, 'title', None) or getattr(chat, 'first_name', 'Private Chat')

    if hasattr(chat, 'type'):
        chat_type_enum = chat.type
        if hasattr(chat_type_enum, 'value'):
            chat_type = chat_type_enum.value
        else:
            chat_type = str(chat_type_enum).lower()

            if chat_type.startswith('chattype.'):
                chat_type = chat_type[9:]
    else:
        if chat_id > 0:
            chat_type = "private"
        else:
            chat_type = "group"

    return chat_id, chat_title, chat_type


def format_event_message(
    event_name: str,
    description: Optional[str],
    event_datetime: datetime,
    end_datetime: Optional[datetime] = None,
    reminder_times: Optional[List[str]] = None
) -> str:
    """Format event message for Telegram."""
    # Convert to local timezone for display
    local_tz = pytz.timezone(settings.timezone)

    # Convert event datetime to local timezone
    if event_datetime.tzinfo is None:
        # Assume UTC if naive
        event_datetime = pytz.UTC.localize(event_datetime)
    local_event_datetime = event_datetime.astimezone(local_tz)

    # Convert end datetime to local timezone if provided
    local_end_datetime = None
    if end_datetime:
        if end_datetime.tzinfo is None:
            # Assume UTC if naive
            end_datetime = pytz.UTC.localize(end_datetime)
        local_end_datetime = end_datetime.astimezone(local_tz)

    # Header
    lines = [
        "📅 **СОБЫТИЕ СОЗДАНО**",
        "",
        f"**{event_name}**"
    ]

    # Description
    if description:
        lines.extend(["", description])

    # Timing
    if local_end_datetime:
        # Format start and end times
        start_str = local_event_datetime.strftime("%H:%M")
        end_str = local_end_datetime.strftime("%H:%M")
        date_str = local_event_datetime.strftime("%Y-%m-%d")
        lines.append(f"⏰ **Время:** {date_str} {start_str} - {end_str}")
    else:
        # Single time
        time_str = local_event_datetime.strftime("%Y-%m-%d %H:%M")
        lines.append(f"⏰ **Время:** {time_str}")

    # Time remaining
    time_remaining = format_time_remaining(event_datetime)
    lines.append(f"⏳ **{time_remaining}**")

    # Reminders
    if reminder_times:
        reminder_str = ", ".join(reminder_times)
        lines.append(f"🔔 **Напоминания:** {reminder_str}")

    return "\n".join(lines)


def format_time_remaining(target_datetime: datetime) -> str:
    """Format time remaining until target datetime."""
    now = datetime.utcnow()

    # Ensure both datetimes are timezone-aware or naive
    if target_datetime.tzinfo is not None and now.tzinfo is None:
        # Convert naive now to UTC timezone
        import pytz
        now = pytz.UTC.localize(now)
    elif target_datetime.tzinfo is None and now.tzinfo is not None:
        # Convert timezone-aware now to naive
        now = now.replace(tzinfo=None)

    if target_datetime <= now:
        return "⏰ Сейчас"

    delta = target_datetime - now

    if delta.days > 0:
        return f"⏰ {delta.days}д {delta.seconds // 3600}ч"
    elif delta.seconds >= 3600:
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        return f"⏰ {hours}ч {minutes}м"
    else:
        minutes = delta.seconds // 60
        return f"⏰ {minutes}м"


# def format_pinned_event_message(
#     event_name: str,
#     description: Optional[str],
#     event_datetime: datetime,
#     end_datetime: Optional[datetime] = None
# ) -> str:
#     """Format simple pinned event message without reminders."""
#     # Convert to local timezone for display
#     local_tz = pytz.timezone(settings.timezone)

#     # Convert event datetime to local timezone
#     if event_datetime.tzinfo is None:
#         # Assume UTC if naive
#         event_datetime = pytz.UTC.localize(event_datetime)
#     local_event_datetime = event_datetime.astimezone(local_tz)

#     # Convert end datetime to local timezone if provided
#     local_end_datetime = None
#     if end_datetime:
#         if end_datetime.tzinfo is None:
#             # Assume UTC if naive
#             end_datetime = pytz.UTC.localize(end_datetime)
#         local_end_datetime = end_datetime.astimezone(local_tz)

#     # Header
#     lines = [
#         "📅 **СОБЫТИЕ**",
#         "",
#         f"**{event_name}**"
#     ]

#     # Description
#     if description:
#         lines.extend(["", description])

#     # Timing
#     if local_end_datetime:
#         # Format start and end times
#         start_str = local_event_datetime.strftime("%H:%M")
#         end_str = local_end_datetime.strftime("%H:%M")
#         date_str = local_event_datetime.strftime("%Y-%m-%d")
#         lines.append(f"⏰ **Время:** {date_str} {start_str} - {end_str}")
#     else:
#         # Single time
#         time_str = local_event_datetime.strftime("%Y-%m-%d %H:%M")
#         lines.append(f"⏰ **Время:** {time_str}")

