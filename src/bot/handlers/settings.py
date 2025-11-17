from aiogram.types import Message, CallbackQuery
from aiogram.types.user import User

from ...services.user_settings_service import UserSettingsService
from ...utils.logger import setup_logger
from ..keyboards import KeyboardBuilder

logger = setup_logger(__name__)

class SettingsHandlers:
    """Handlers for settings-related commands."""

    def __init__(self, user_settings_service: UserSettingsService):
        self.user_settings_service = user_settings_service

    async def handle_settings(self, message: Message, user: User, to_answer: bool = True) -> None:
        try:
            logger.info(f"Going to settings page: {user.id}")
            owner_settings = await self.user_settings_service.get_owner_settings()
            settings_text = self.user_settings_service.generate_user_settings_text(owner_settings)
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

            action = parts[1]
            await callback.answer()

            if action == "reminders":
                await callback.message.answer(
                    "Введите команду `/set_reminders 15m,1h,1d` чтобы обновить напоминания.\n"
                    "Значения перечисляются через запятую.\n"
                    "Поддерживаемые единицы: `m`, `h`, `d`.\n"
                    "_Пример:_ `/set_reminders 10m,30m,2h`",
                    parse_mode="Markdown"
                )
                return

            if action == "date":
                await callback.message.answer(
                    "Введите команду `/set_date_format %d.%m.%Y %H:%M` чтобы обновить формат даты.\n"
                    "Используются стандартные плейсхолдеры Python `strftime`.",
                    parse_mode="Markdown"
                )
                return

            if action == "birthday":
                await callback.message.answer(
                    "Введите команду `/set_birthday YYYY-MM-DD` чтобы сохранить дату рождения.\n"
                    "Используйте `clear`, чтобы удалить значение.\n"
                    "_Пример:_ `/set_birthday 1990-05-17`",
                    parse_mode="Markdown"
                )
                return

            if action == "timezone":
                await callback.message.answer("Изменение часового пояса пока не реализовано.")
                return

            await callback.message.answer("⚠️ Эта настройка ещё не поддерживается.")

        except Exception as e:
            logger.error(f"Error in settings callback: {e}")
            await callback.answer("❌ Не удалось обработать запрос к настройкам", show_alert=True)

    async def handle_set_birthday_command(self, message: Message) -> None:
        argument = self._extract_argument(message)
        try:
            updated = await self.user_settings_service.update_owner_birthday(argument)
        except ValueError as exc:
            await message.answer(f"❌ {exc}")
            return

        birthday_text = (
            updated.birthday.strftime("%Y-%m-%d") if updated.birthday else "Не указана"
        )
        await message.answer(f"🎂 День рождения обновлён: {birthday_text}")

    async def handle_set_reminders_command(self, message: Message) -> None:
        argument = self._extract_argument(message)
        try:
            updated = await self.user_settings_service.update_owner_default_reminders(argument)
        except ValueError as exc:
            await message.answer(f"❌ {exc}")
            return

        reminders = self.user_settings_service.format_reminder_times(updated.default_reminder_times)
        reminder_text = ", ".join(reminders) if reminders else "Не заданы"
        await message.answer(f"🔔 Напоминания по умолчанию обновлены: {reminder_text}")

    async def handle_set_date_format_command(self, message: Message) -> None:
        argument = self._extract_argument(message)
        try:
            updated = await self.user_settings_service.update_owner_date_format(argument)
        except ValueError as exc:
            await message.answer(f"❌ {exc}")
            return

        await message.answer(f"🗓 Формат даты обновлён: `{updated.date_format}`", parse_mode="Markdown")

    def _extract_argument(self, message: Message) -> str:
        if not message.text:
            return ""
        parts = message.text.split(maxsplit=1)
        return parts[1].strip() if len(parts) > 1 else ""
