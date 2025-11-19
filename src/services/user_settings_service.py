from datetime import datetime
from typing import Iterable, List

from .service import Service
from ..models import UserSettings
from ..config.settings import settings
from ..utils.logger import setup_logger
from ..utils.helpers import parse_reminder_time

logger = setup_logger(__name__)


class UserSettingsService(Service):
    def __init__(self):
        super().__init__(logger)

    async def get_user_settings(self, user_id: int) -> UserSettings:
        defaults = {
            'timezone': settings.timezone,
            'default_reminder_times': self._normalize_reminder_values(
                settings.default_reminder_times,
                allow_empty=True
            )
        }
        user_settings, created = await UserSettings.get_or_create(
            user_id=user_id,
            defaults=defaults
        )
        if created:
            logger.info(f"Created default settings for user {user_id}")
        else:
            logger.info(f"Already created for user: {user_id}")

        normalized_current = self._normalize_reminder_values(
            user_settings.default_reminder_times,
            allow_empty=True
        )
        if normalized_current and normalized_current != user_settings.default_reminder_times:
            user_settings.default_reminder_times = normalized_current
            await user_settings.save(update_fields=["default_reminder_times"])

        return user_settings

    async def get_owner_settings(self) -> UserSettings:
        return await self.get_user_settings(settings.owner_user_id)

    async def update_owner_birthday(self, birthday_text: str) -> UserSettings:
        birthday_text = (birthday_text or "").strip()
        owner_settings = await self.get_owner_settings()

        if birthday_text.lower() in {"", "clear", "reset"}:
            owner_settings.birthday = None
            await owner_settings.save(update_fields=["birthday"])
            return owner_settings

        try:
            birthday_date = datetime.strptime(birthday_text, "%Y-%m-%d").date()
        except ValueError as exc:
            raise ValueError("Используйте формат YYYY-MM-DD (например, 1990-05-17)") from exc

        owner_settings.birthday = birthday_date
        await owner_settings.save(update_fields=["birthday"])
        return owner_settings

    async def update_owner_default_reminders(self, reminder_text: str) -> UserSettings:
        reminders = self._parse_reminder_input(reminder_text)
        owner_settings = await self.get_owner_settings()
        owner_settings.default_reminder_times = reminders
        await owner_settings.save(update_fields=["default_reminder_times"])
        return owner_settings

    async def update_owner_date_format(self, date_format: str) -> UserSettings:
        date_format = (date_format or "").strip()
        if not date_format:
            raise ValueError("Формат даты не может быть пустым")

        owner_settings = await self.get_owner_settings()
        owner_settings.date_format = date_format
        await owner_settings.save(update_fields=["date_format"])
        return owner_settings

    def generate_user_settings_text(self, user_settings: UserSettings) -> str:
        reminder_times = self._format_reminder_times(user_settings.default_reminder_times)
        birthday_text = (
            user_settings.birthday.strftime("%Y-%m-%d")
            if user_settings.birthday
            else "Не указана"
        )
        # last_sync = "Никогда"
        # if user_settings.last_calendar_sync:
        #     last_sync = user_settings.last_calendar_sync.strftime("%Y-%m-%d %H:%M")
        settings_text = f"""
⚙️ **Ваши настройки**

🔔 **Напоминания по умолчанию:** {', '.join(reminder_times) if reminder_times else "Не заданы"}
🌍 **Часовой пояс:** {user_settings.timezone}
📅 **Формат даты:** {user_settings.date_format}
🎂 **День рождения:** {birthday_text}

🔕 **Уведомления:**
• Напоминания: {"✅ Включены" if user_settings.reminder_notifications else "❌ Отключены"}
• Уведомления о завершении: {"✅ Включены" if user_settings.completion_notifications else "❌ Отключены"}

Используйте кнопки ниже для изменения настроек.
"""
        return settings_text

    def _normalize_reminder_values(
        self,
        values: Iterable,
        allow_empty: bool = False
    ) -> List[int]:
        normalized: List[int] = []
        if not values:
            return [] if allow_empty else normalized

        for item in values:
            if item is None:
                continue
            if isinstance(item, int):
                normalized.append(item)
            elif isinstance(item, (float,)):
                normalized.append(int(item))
            elif isinstance(item, str):
                stripped = item.strip()
                if not stripped:
                    continue
                normalized.append(parse_reminder_time(stripped))
            else:
                raise ValueError(f"Unsupported reminder type: {type(item)}")

        if not normalized and not allow_empty:
            raise ValueError("Не удалось распознать список напоминаний")

        return normalized

    def _parse_reminder_input(self, reminder_text: str) -> List[int]:
        reminder_text = (reminder_text or "").strip()
        if not reminder_text:
            raise ValueError("Укажите значения через запятую, например: 15m, 1h, 1d")

        tokens = [token.strip() for token in reminder_text.split(",") if token.strip()]
        if not tokens:
            raise ValueError("Укажите хотя бы одно значение напоминания")

        return self._normalize_reminder_values(tokens)

    def _format_reminder_times(self, reminder_values: Iterable) -> List[str]:
        formatted: List[str] = []
        if not reminder_values:
            return formatted

        normalized = self._normalize_reminder_values(reminder_values, allow_empty=True)
        for minutes in normalized:
            if minutes < 60:
                formatted.append(f"{minutes}м")
            elif minutes % 60 == 0:
                hours = minutes // 60
                formatted.append(f"{hours}ч")
            else:
                hours, mins = divmod(minutes, 60)
                formatted.append(f"{hours}ч {mins}м")
        return formatted

    def format_reminder_times(self, reminder_values: Iterable) -> List[str]:
        """Public helper for UI layers."""
        return self._format_reminder_times(reminder_values)
