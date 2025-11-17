from aiogram.types import Message, CallbackQuery
from aiogram.types.user import User
from typing import List, Optional
import pytz

from ...models import Event
from ...utils.logger import setup_logger
from ...utils.helpers import format_time_remaining
from ...config.settings import settings
from ..keyboards import KeyboardBuilder
from ...services.user_settings_service import UserSettingsService
from ...services.event_service import EventService

logger = setup_logger(__name__)


class EventHandlers:
    def __init__(self, user_settings_service: UserSettingsService, event_service: EventService):
        self.user_settings_service = user_settings_service
        self.event_service = event_service

    async def handle_start(self, message: Message, user: User, to_answer: bool = True) -> None:
        try:
            user_name = user.first_name or "User"

            markup, welcome_text = KeyboardBuilder.main_menu()
            handle_method = message.answer if to_answer else message.edit_text
            await handle_method(
                welcome_text.format(user_name=user_name),
                reply_markup=markup,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error in start handler: {e}")
            await message.answer("❌ Произошла ошибка. Попробуйте ещё раз.")

    async def handle_help(self, message: Message, user: User, to_answer: bool = True) -> None:
        try:
            markup, help_text = KeyboardBuilder.help_menu()
            handle_method = message.answer if to_answer else message.edit_text
            await handle_method(
                help_text,
                reply_markup=markup,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error in help handler: {e}")
            await message.answer("❌ Произошла ошибка. Попробуйте ещё раз.")

    async def handle_list_events(self, message: Message, user: User, to_answer: bool = True) -> None:
        try:
            handle_method = message.answer if to_answer else message.edit_text

            events = await self.event_service.get_user_events(
                user_id=user.id,
                active_only=True
            )
            if not events:
                await handle_method(
                    "📅 **Нет активных событий**\n\n"
                    "У вас нет активных событий. Создайте событие с помощью:\n"
                    "`++event завтра 15:00 Встреча`",
                    reply_markup=KeyboardBuilder.empty_list("main_menu"),
                    parse_mode="Markdown"
                )
                return

            user_settings = await self.user_settings_service.get_user_settings(user.id)
            events_text = self._format_events_list(user_settings.timezone, events)
            await handle_method(
                events_text,
                reply_markup=KeyboardBuilder.event_list(events),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error listing events: {e}")
            await message.answer("❌ Не удалось загрузить события. Попробуйте ещё раз.")

    def _format_events_list(self, timezone, events: List[Event]) -> str:
        if not events:
            return "📅 **События не найдены**"

        # Get local timezone
        local_tz = pytz.timezone(timezone)

        lines = ["📅 **Ваши события**", ""]
        for i, event in enumerate(events[:10], 1):
            # Convert to local timezone
            if event.event_datetime.tzinfo is None:
                event_datetime = pytz.UTC.localize(event.event_datetime)
            else:
                event_datetime = event.event_datetime
            local_event_datetime = event_datetime.astimezone(local_tz)

            time_str = local_event_datetime.strftime("%m/%d %H:%M")
            if event.end_datetime:
                if event.end_datetime.tzinfo is None:
                    end_datetime = pytz.UTC.localize(event.end_datetime)
                else:
                    end_datetime = event.end_datetime
                local_end_datetime = end_datetime.astimezone(local_tz)
                end_str = local_end_datetime.strftime("%H:%M")
                time_str += f"-{end_str}"
            time_remaining = format_time_remaining(event.event_datetime)
            status_icon = "🟢" if not event.is_overdue else "🔴"
            event_line = f"{status_icon} **{event.event_name}**"
            time_line = f"   📅 {time_str} • {time_remaining}"
            lines.extend([event_line, time_line])
            if i < len(events):
                lines.append("")
        if len(events) > 10:
            lines.append(f"... и ещё {len(events) - 10} событий")
        return "\n".join(lines)
