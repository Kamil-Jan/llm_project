from aiogram.types import Message, CallbackQuery
from aiogram.types.user import User

from ...models import UserSettings
from ...config.settings import settings
from ...utils.logger import setup_logger
from ..keyboards import KeyboardBuilder

logger = setup_logger(__name__)

class SettingsHandlers:
    """Handlers for settings-related commands."""

    def __init__(self):
        pass

    async def handle_settings(self, message: Message, user: User, to_answer: bool = True) -> None:
        try:
            logger.info(f"Going to settings page: {user.id}")
            user_settings = await self.get_user_settings(user.id)
            settings_text = self._format_settings_display(user_settings)
            handle_method = message.answer if to_answer else message.edit_text
            await handle_method(
                settings_text,
                reply_markup=KeyboardBuilder.settings_menu(),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error in settings handler: {e}")
            await message.answer("❌ Не удалось загрузить настройки. Попробуйте ещё раз.")

    async def handle_settings_menu(self, message: Message) -> None:
        await self.handle_settings(message, message.from_user, to_answer=True)

    async def handle_settings_callback(self, callback: CallbackQuery) -> None:
        try:
            data = callback.data
            if not data:
                await callback.answer("Неверные данные колбэка")
                return

            parts = data.split("_")
            if len(parts) == 1:
                await callback.answer()
                await self.handle_settings(callback.message, callback.from_user, to_answer=False)
                return

            # TODO add settings change
            await callback.answer("❌ TODO", show_alert=True)

        except Exception as e:
            logger.error(f"Error in settings callback: {e}")
            await callback.answer("❌ Не удалось обработать запрос к настройкам", show_alert=True)

    def _format_settings_display(self, user_settings: UserSettings) -> str:
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
