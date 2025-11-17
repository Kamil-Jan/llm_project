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
            user_settings = await self.user_settings_service.get_user_settings(user.id)
            settings_text = self.user_settings_service.generate_user_settings_text(user_settings)
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
