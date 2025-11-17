from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..models import Event
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class KeyboardBuilder:
    @classmethod
    def main_menu(cls) -> tuple[InlineKeyboardMarkup, str]:
        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(text="📅 Мои события", callback_data="list_events"),
            #InlineKeyboardButton(text="🔄 Синхронизация календаря", callback_data="sync_calendar"),
        )
        builder.row(
            InlineKeyboardButton(text="❓ Помощь", callback_data="help"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
        )

        welcome_text = """
🎯 **Добро пожаловать в project, {user_name}!**

Я ваш персональный помощник по управлению временем. Я помогаю управлять событиями прямо в чатах Telegram с умной интеграцией календаря.

**Основные функции:**
• Создание событий командой `++event` в любом чате
• Распознавание дат на естественном языке
• Синхронизация с Apple Calendar
• Умные уведомления-напоминания
• Красивый интерфейс управления событиями

**Быстрый старт:**
1. В любом чате введите: `++event завтра 15:00 Встреча команды`
2. Я создам, отформатирую и закреплю сообщение о событии
3. Используйте этот чат с ботом для управления всеми событиями

Готовы организоваться? 🚀
"""
        return builder.as_markup(), welcome_text

    @classmethod
    def help_menu(self) -> tuple[InlineKeyboardMarkup, str]:
        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
        )

        help_text = """
📚 **Помощь TimeAssist**

**Создание событий:**
В любом чате используйте команду `++event`:

`++event завтра 15:00 Встреча команды`
`++event пятница 14:00-16:00 Презентация клиенту --remind 1h,15m`
`++event следующий понедельник 9:00 Ежедневная планёрка`

**Естественный язык:**
• "завтра", "на следующей неделе", "через 2 часа"
• "15:00-16:00" для продолжительности
• "--remind 30m,1h" для настройки напоминаний

**Команды бота:**
• `/events` - Управление событиями
• `/settings` - Настройки
• `/sync` - Синхронизация с Apple Calendar
• `/help` - Показать справку

**Возможности:**
• 📌 Автоматическое закрепление сообщений
• 🔔 Умные напоминания
• 📅 Синхронизация с Apple Calendar
• ✏️ Редактирование/перенос событий
• 🎯 48-часовое ограничение редактирования
"""
        return builder.as_markup(), help_text

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
            InlineKeyboardButton(text="🗓 Формат даты", callback_data="settings_date_format"),
        )
        builder.row(
            InlineKeyboardButton(text="🎂 День рождения", callback_data="settings_birthday"),
        )
        builder.row(
            InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu")
        )

        return builder.as_markup()

    def empty_list(self, back_callback: str = "main_menu") -> InlineKeyboardMarkup:
        """Build keyboard for empty lists."""
        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(text="🔙 Назад", callback_data=back_callback)
        )

        return builder.as_markup()

    def event_list(events: List[Event], page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        start_idx = page * per_page
        end_idx = min(start_idx + per_page, len(events))
        page_events = events[start_idx:end_idx]

        for event in page_events:
            event_text = f"📅 {event.event_name}"
            if len(event_text) > 30:
                event_text = event_text[:27] + "..."

            builder.row(
                InlineKeyboardButton(
                    text=event_text,
                    callback_data=f"event_details:{event.id}"
                )
            )

        pagination_buttons = []

        if page > 0:
            pagination_buttons.append(
                InlineKeyboardButton(text="◀️ Назад", callback_data=f"events_page:{page-1}")
            )

        if end_idx < len(events):
            pagination_buttons.append(
                InlineKeyboardButton(text="Далее ▶️", callback_data=f"events_page:{page+1}")
            )

        if pagination_buttons:
            builder.row(*pagination_buttons)

        builder.row(
            InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu")
        )

        return builder.as_markup()
