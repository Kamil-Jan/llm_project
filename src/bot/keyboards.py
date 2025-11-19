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
🎯 Добро пожаловать в AstroBot, {user_name}!

Я — ваш умный помощник для управления встречами и событиями прямо в Telegram.
Создаю события по голосовым сообщениям, понимаю естественный язык, поддерживаю команду `++event`
и дополнительно проверяю астрологическую благоприятность выбранного времени.

✨ Основные возможности:
• 📅 Создание событий командой `++event` в любом чате  
• 🎤 Создание событий по голосовым сообщениям в любом чате — я сам распознаю и пойму текст  
• 🧠 Понимание естественного языка: «встреча завтра в 14 возле офиса»  
• 🔄 Автоматическая синхронизация с Google Calendar  
• 🔔 Умные напоминания о приближающихся встречах  
• 🔮 Проверка астрологической благоприятности даты и времени события  
• 📌 Красивые форматированные карточки событий в чате  

🚀 Как начать:
1. Напишите: `++event завтра 15:00 встреча с командой`  
   или просто отправьте голосовое с описанием встречи.  
2. Я создам и оформлю событие, проверю астрологическую благоприятность
   и добавлю его в ваш Google Calendar.  
3. Используйте этот чат, чтобы просматривать, редактировать и управлять всеми встречами.

Готовы сделать своё расписание удачным по версии вселенной? 🗓️✨
"""
        return builder.as_markup(), welcome_text

    @classmethod
    def help_menu(self) -> tuple[InlineKeyboardMarkup, str]:
        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
        )

        help_text = """
📚 **Справка — AstroBot**

### ✨ Создание событий
Вы можете создавать события двумя способами:

**1) Через команду `++event`:**  
`++event завтра 15:00 встреча команды`  
`++event пятница 14:00-16:00 презентация клиенту --remind 1h,15m`  
`++event следующий понедельник 9:00 планёрка`

**2) Просто отправьте голосовое:**  
Я распознаю текст и создам событие автоматически.

---

### 🧠 Понимание естественного языка
Я понимаю такие формулировки:
• «завтра», «через 2 часа», «в следующий вторник»  
• интервалы: `15:00-16:00`  
• напоминания: `--remind 30m,1h`  
• голосовое описание встречи: *«встреча завтра в 11 у офиса»*

---

### 🛠 Команды бота
• `/events` — список и управление вашими событиями  
• `/settings` — настройки бота  
• `/sync` — синхронизация с Google Calendar  
• `/help` — показать справку  

---

### 📅 Возможности TimeAssist
• 🎤 Создание событий по голосовым сообщениям  
• 📅 Синхронизация с Google Calendar  
• 📌 Автоматическое закрепление карточек событий  
• 🔔 Умные напоминания  
• ✏️ Редактирование и перенос событий  
• ✨ Оценка благоприятности выбранного момента  
• ⏳ Ограничение редактирования событий: 48 часов  

Если хотите, я могу подробнее рассказать о любой функции — просто спросите!
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
