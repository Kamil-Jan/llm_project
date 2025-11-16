from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

#from ..models import Event
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class KeyboardBuilder:
    @classmethod
    def main_menu(cls) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(text="❓ Помощь", callback_data="help"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
        )
        #builder.row(
            #InlineKeyboardButton(text="📅 Мои события", callback_data="list_events"),
            #InlineKeyboardButton(text="🔄 Синхронизация календаря", callback_data="sync_calendar"),
        #)

        return builder.as_markup()

    @classmethod
    def help_menu(cls) -> InlineKeyboardMarkup:
        """Build help menu."""
        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
        )

        return builder.as_markup()

    @classmethod
    def settings_menu(cls) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(text="🔔 Напоминания по умолчанию", callback_data="settings_reminders"),
        )
        builder.row(
            InlineKeyboardButton(text="🌍 Часовой пояс", callback_data="settings_timezone"),
        )
        builder.row(
            InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu")
        )

        return builder.as_markup()

    # @classmethod
    # def event_list(cls, events: List[Event], page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
    #     """Build event list keyboard with pagination."""
    #     builder = InlineKeyboardBuilder()

    #     # Calculate pagination
    #     start_idx = page * per_page
    #     end_idx = min(start_idx + per_page, len(events))
    #     page_events = events[start_idx:end_idx]

    #     # Add event buttons
    #     for event in page_events:
    #         # Format event button text
    #         event_text = f"📅 {event.event_name}"
    #         if len(event_text) > 30:
    #             event_text = event_text[:27] + "..."

    #         builder.row(
    #             InlineKeyboardButton(
    #                 text=event_text,
    #                 callback_data=f"event_details:{event.id}"
    #             )
    #         )

    #     # Add pagination buttons
    #     pagination_buttons = []

    #     if page > 0:
    #         pagination_buttons.append(
    #             InlineKeyboardButton(text="◀️ Назад", callback_data=f"events_page:{page-1}")
    #         )

    #     if end_idx < len(events):
    #         pagination_buttons.append(
    #             InlineKeyboardButton(text="Далее ▶️", callback_data=f"events_page:{page+1}")
    #         )

    #     if pagination_buttons:
    #         builder.row(*pagination_buttons)

    #     # Add back button
    #     builder.row(
    #         InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu")
    #     )

    #     return builder.as_markup()

    # @classmethod
    # def event_management(cls, event_id: int) -> InlineKeyboardMarkup:
    #     """Build event management keyboard for bot's private chat."""
    #     builder = InlineKeyboardBuilder()

    #     # Event actions
    #     builder.row(
    #         InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_event:{event_id}"),
    #         InlineKeyboardButton(text="✅ Завершить", callback_data=f"complete_event:{event_id}")
    #     )
    #     builder.row(
    #         InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_event:{event_id}")
    #     )

    #     return builder.as_markup()

    # @classmethod
    # def event_details(cls, event: Event) -> InlineKeyboardMarkup:
    #     """Build event details keyboard."""
    #     builder = InlineKeyboardBuilder()

    #     # Event actions
    #     builder.row(
    #         InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_event:{event.id}")
    #     )

    #     # Status actions
    #     if not event.is_completed:
    #         builder.row(
    #             InlineKeyboardButton(text="✅ Отметить выполненным", callback_data=f"complete_event:{event.id}"),
    #             InlineKeyboardButton(text="❌ Отменить событие", callback_data=f"cancel_event:{event.id}")
    #         )

    #     # Calendar sync
    #     if event.calendar_event_id:
    #         builder.row(
    #             InlineKeyboardButton(text="🔄 Обновить календарь", callback_data=f"sync_event:{event.id}")
    #         )
    #     else:
    #         builder.row(
    #             InlineKeyboardButton(text="📅 Добавить в календарь", callback_data=f"add_to_calendar:{event.id}")
    #         )

    #     # Navigation
    #     builder.row(
    #         InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_event:{event.id}"),
    #         InlineKeyboardButton(text="🔙 Назад", callback_data="list_events")
    #     )

    #     return builder.as_markup()

    # @classmethod
    # def event_edit_menu(cls, event: Event) -> InlineKeyboardMarkup:
    #     """Build event editing menu."""
    #     builder = InlineKeyboardBuilder()

    #     builder.row(
    #         InlineKeyboardButton(text="📝 Редактировать название", callback_data=f"edit_name:{event.id}"),
    #         InlineKeyboardButton(text="📄 Редактировать описание", callback_data=f"edit_description:{event.id}")
    #     )
    #     builder.row(
    #         InlineKeyboardButton(text="⏰ Редактировать время", callback_data=f"edit_time:{event.id}"),
    #         InlineKeyboardButton(text="🔔 Редактировать напоминания", callback_data=f"edit_reminders:{event.id}")
    #     )
    #     builder.row(
    #         InlineKeyboardButton(text="💾 Сохранить изменения", callback_data=f"save_event:{event.id}"),
    #         InlineKeyboardButton(text="❌ Отмена", callback_data=f"event_details:{event.id}")
    #     )

    #     return builder.as_markup()

    # @classmethod
    # def confirmation(cls, action: str, target_id: int, confirm_text: str = "Да", cancel_text: str = "Нет") -> InlineKeyboardMarkup:
    #     """Build confirmation keyboard."""
    #     builder = InlineKeyboardBuilder()

    #     builder.row(
    #         InlineKeyboardButton(text=f"✅ {confirm_text}", callback_data=f"confirm_{action}:{target_id}"),
    #         InlineKeyboardButton(text=f"❌ {cancel_text}", callback_data=f"cancel_{action}:{target_id}")
    #     )

    #     return builder.as_markup()

    # @classmethod
    # def reminder_times_selection(cls, current_times: List[int]) -> InlineKeyboardMarkup:
    #     """Build reminder times selection keyboard."""
    #     builder = InlineKeyboardBuilder()

    #     # Common reminder times in minutes
    #     common_times = [5, 15, 30, 60, 120, 360, 720, 1440]  # 5m, 15m, 30m, 1h, 2h, 6h, 12h, 1d

    #     for minutes in common_times:
    #         # Format time display
    #         if minutes < 60:
    #             time_text = f"{minutes}m"
    #         elif minutes < 1440:
    #             hours = minutes // 60
    #             time_text = f"{hours}h"
    #         else:
    #             days = minutes // 1440
    #             time_text = f"{days}d"

    #         # Check if already selected
    #         is_selected = minutes in current_times
    #         prefix = "✅" if is_selected else "⚪"

    #         builder.row(
    #             InlineKeyboardButton(
    #                 text=f"{prefix} {time_text}",
    #                 callback_data=f"toggle_reminder:{minutes}"
    #             )
    #         )

    #     # Custom time option
    #     builder.row(
    #         InlineKeyboardButton(text="➕ Пользовательское время", callback_data="custom_reminder")
    #     )

    #     # Navigation
    #     builder.row(
    #         InlineKeyboardButton(text="💾 Сохранить", callback_data="save_reminders"),
    #         InlineKeyboardButton(text="❌ Отмена", callback_data="settings")
    #     )

    #     return builder.as_markup()

    # @classmethod
    # def timezone_selection(cls, current_timezone: str) -> InlineKeyboardMarkup:
    #     """Build timezone selection keyboard."""
    #     builder = InlineKeyboardBuilder()

    #     # Common timezones
    #     timezones = [
    #         ("UTC", "UTC"),
    #         ("Europe/Moscow", "Moscow"),
    #         ("Europe/London", "London"),
    #         ("Europe/Berlin", "Berlin"),
    #         ("America/New_York", "New York"),
    #         ("America/Los_Angeles", "Los Angeles"),
    #         ("Asia/Tokyo", "Tokyo"),
    #         ("Asia/Shanghai", "Shanghai")
    #     ]

    #     for tz_id, tz_name in timezones:
    #         prefix = "✅" if tz_id == current_timezone else "⚪"

    #         builder.row(
    #             InlineKeyboardButton(
    #                 text=f"{prefix} {tz_name}",
    #                 callback_data=f"set_timezone:{tz_id}"
    #             )
    #         )

    #     # Navigation
    #     builder.row(
    #         InlineKeyboardButton(text="🔙 Назад", callback_data="settings")
    #     )

    #     return builder.as_markup()

    # @classmethod
    # def calendar_sync_menu(cls) -> InlineKeyboardMarkup:
    #     """Build calendar sync menu."""
    #     builder = InlineKeyboardBuilder()

    #     builder.row(
    #         InlineKeyboardButton(text="🔄 Синхронизировать сейчас", callback_data="sync_now"),
    #         InlineKeyboardButton(text="📊 Статус синхронизации", callback_data="sync_status")
    #     )
    #     builder.row(
    #         InlineKeyboardButton(text="⚙️ Настройки синхронизации", callback_data="sync_settings"),
    #         InlineKeyboardButton(text="🔙 Назад", callback_data="settings")
    #     )

    #     return builder.as_markup()

    # @classmethod
    # def empty_list(cls, back_callback: str = "main_menu") -> InlineKeyboardMarkup:
    #     """Build keyboard for empty lists."""
    #     builder = InlineKeyboardBuilder()

    #     builder.row(
    #         InlineKeyboardButton(text="🔙 Назад", callback_data=back_callback)
    #     )

    #     return builder.as_markup()

    # @classmethod
    # def help_menu(cls) -> InlineKeyboardMarkup:
    #     """Build help menu."""
    #     builder = InlineKeyboardBuilder()

    #     builder.row(
    #         InlineKeyboardButton(text="📝 Команды событий", callback_data="help_commands"),
    #         InlineKeyboardButton(text="🔧 Возможности бота", callback_data="help_features")
    #     )
    #     builder.row(
    #         InlineKeyboardButton(text="❓ Часто задаваемые вопросы", callback_data="help_faq"),
    #         InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
    #     )

    #     return builder.as_markup()

    # @classmethod
    # def close_keyboard(cls) -> InlineKeyboardMarkup:
    #     """Build simple close keyboard."""
    #     builder = InlineKeyboardBuilder()

    #     builder.row(
    #         InlineKeyboardButton(text="❌ Закрыть", callback_data="close_message")
    #     )

    #     return builder.as_markup()

    # @classmethod
    # def edit_name_keyboard(cls, event_id: int) -> InlineKeyboardMarkup:
    #     """Build keyboard for editing event name."""
    #     builder = InlineKeyboardBuilder()

    #     builder.row(
    #         InlineKeyboardButton(text="❌ Отмена", callback_data=f"event_details:{event_id}")
    #     )

    #     return builder.as_markup()

    # @classmethod
    # def edit_description_keyboard(cls, event_id: int) -> InlineKeyboardMarkup:
    #     """Build keyboard for editing event description."""
    #     builder = InlineKeyboardBuilder()

    #     builder.row(
    #         InlineKeyboardButton(text="❌ Отмена", callback_data=f"event_details:{event_id}")
    #     )

    #     return builder.as_markup()

    # @classmethod
    # def edit_time_keyboard(cls, event_id: int) -> InlineKeyboardMarkup:
    #     """Build keyboard for editing event time."""
    #     builder = InlineKeyboardBuilder()

    #     builder.row(
    #         InlineKeyboardButton(text="❌ Отмена", callback_data=f"event_details:{event_id}")
    #     )

    #     return builder.as_markup()

    # @classmethod
    # def edit_reminders_keyboard(cls, event_id: int) -> InlineKeyboardMarkup:
    #     """Build keyboard for editing event reminders."""
    #     builder = InlineKeyboardBuilder()

    #     builder.row(
    #         InlineKeyboardButton(text="❌ Отмена", callback_data=f"event_details:{event_id}")
    #     )

    #     return builder.as_markup()
