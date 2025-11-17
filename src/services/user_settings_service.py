from .service import Service
from ..models import UserSettings
from ..config.settings import settings
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class UserSettingsService(Service):
    def __init__(self):
        super().__init__(logger)

    async def get_user_settings(self, user_id: int) -> UserSettings:
        user_settings, created = await UserSettings.get_or_create(
            user_id=user_id,
            defaults={
                'timezone': settings.timezone,
                'default_reminder_times': settings.default_reminder_times
            }
        )
        if created:
            logger.info(f"Created default settings for user {user_id}")
        else:
            logger.info(f"Already created for user: {user_id}")
        return user_settings

    def generate_user_settings_text(self, user_settings: UserSettings) -> str:
        reminder_times = []
        for minutes in user_settings.default_reminder_times:
            if isinstance(minutes, str):
                reminder_times.append(minutes)
            else:
                if minutes < 60:
                    reminder_times.append(f"{minutes}m")
                elif minutes % 60 == 0:
                    reminder_times.append(f"{minutes//60}h")
                else:
                    h, m = divmod(minutes, 60)
                    reminder_times.append(f"{h}h{m}m")
        # last_sync = "Никогда"
        # if user_settings.last_calendar_sync:
        #     last_sync = user_settings.last_calendar_sync.strftime("%Y-%m-%d %H:%M")
        settings_text = f"""
⚙️ **Ваши настройки**

🔔 **Напоминания по умолчанию:** {', '.join(reminder_times)}
🌍 **Часовой пояс:** {user_settings.timezone}
📅 **Формат даты:** {user_settings.date_format}

📊 **Интеграция с календарём:**
TODO

🔕 **Уведомления:**
• Напоминания: {"✅ Включены" if user_settings.reminder_notifications else "❌ Отключены"}
• Уведомления о завершении: {"✅ Включены" if user_settings.completion_notifications else "❌ Отключены"}

Используйте кнопки ниже для изменения настроек.
"""
        return settings_text
