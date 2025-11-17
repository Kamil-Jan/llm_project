from typing import Optional
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

from ..services.service import Service
from ..services.user_settings_service import UserSettingsService
from ..services.event_service import EventService
from ..config.settings import settings
from ..utils.logger import setup_logger
from ..utils.exceptions import TelegramError
from ..utils.helpers import is_owner
from .handlers.settings import SettingsHandlers
from .handlers.events import EventHandlers
from .handlers.callbacks import CallbackHandlers


logger = setup_logger(__name__)


class TelegramBot(Service):
    def __init__(self, user_settings_service: UserSettingsService, event_service: EventService):
        super().__init__(logger)
        self.user_settings_service = user_settings_service
        self.event_service = event_service

        self.bot: Optional[Bot] = None
        self.dp: Optional[Dispatcher] = None
        self._running = False

        self.event_handlers: Optional[EventHandlers] = None
        self.settings_handlers: Optional[SettingsHandlers] = None
        self.callback_handlers: Optional[CallbackHandlers] = None

    async def initialize(self):
        await super().initialize()

        try:
            self.bot = Bot(token=settings.telegram_bot_token)
            self.dp = Dispatcher(storage=MemoryStorage())

            self.event_handlers = EventHandlers(
                user_settings_service=self.user_settings_service,
                event_service=self.event_service,
            )

            self.settings_handlers = SettingsHandlers(
                user_settings_service=self.user_settings_service,
            )

            self.callback_handlers = CallbackHandlers()

            self._setup_handlers()

            logger.info("Telegram Bot initialized")

        except Exception as e:
            logger.error(f"Failed to initialize telegram bot: {e}")
            raise TelegramError(f"Failed to initialize telegram bot: {e}")

    async def start(self):
        await super().start()

        if self._running:
            logger.warning("Bot is already running")
            return

        try:
            if not self.bot or not self.dp:
                await self.initialize()

            self._running = True
            logger.info("Starting bot polling...")

            await self.dp.start_polling(self.bot)

        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise TelegramError(f"Bot start failed: {e}")

    async def stop(self):
        await super().stop()

        if not self._running:
            logger.warning("Bot is not running...")
            return

        try:
            await self.bot.session.close()
            self._running = False
            logger.info("Telegram bot stopped")

        except Exception as e:
            logger.error(f"Error stopping bot: {e}")

    def _setup_handlers(self):
        @self.dp.message(Command("start"))
        async def start_command(message: Message):
            if not await self._ensure_owner_message(message):
                return
            await self.event_handlers.handle_start(message, message.from_user, to_answer=True)

        @self.dp.callback_query(F.data.startswith("main_menu"))
        async def main_menu_callback(callback: CallbackQuery):
            if not await self._ensure_owner_callback(callback):
                return
            await callback.answer()
            await self.event_handlers.handle_start(callback.message, callback.from_user, to_answer=False)

        @self.dp.message(Command("help"))
        async def help_command(message: Message):
            if not await self._ensure_owner_message(message):
                return
            await self.event_handlers.handle_help(message, message.from_user, to_answer=True)

        @self.dp.callback_query(F.data.startswith("help"))
        async def help_callback(callback: CallbackQuery):
            if not await self._ensure_owner_callback(callback):
                return
            await callback.answer()
            await self.event_handlers.handle_help(callback.message, callback.from_user, to_answer=False)

        @self.dp.message(Command("settings"))
        async def settings_command(message: Message):
            if not await self._ensure_owner_message(message):
                return
            await self.settings_handlers.handle_settings_menu(message)

        @self.dp.callback_query(F.data.startswith("settings"))
        async def settings_callback(callback: CallbackQuery):
            if not await self._ensure_owner_callback(callback):
                return
            await self.settings_handlers.handle_settings_callback(callback)

        @self.dp.message(Command("events"))
        async def events_command(message: Message):
            if not await self._ensure_owner_message(message):
                return
            await self.event_handlers.handle_list_events(message, message.from_user, to_answer=True)

        @self.dp.callback_query(F.data.startswith("list_events"))
        async def list_events_callback(callback: CallbackQuery):
            if not await self._ensure_owner_callback(callback):
                return
            await self.event_handlers.handle_list_events(callback.message, callback.from_user, to_answer=False)

        @self.dp.message(Command("set_birthday"))
        async def set_birthday_command(message: Message):
            if not await self._ensure_owner_message(message):
                return
            await self.settings_handlers.handle_set_birthday_command(message)

        @self.dp.message(Command("set_reminders"))
        async def set_reminders_command(message: Message):
            if not await self._ensure_owner_message(message):
                return
            await self.settings_handlers.handle_set_reminders_command(message)

        @self.dp.message(Command("set_date_format"))
        async def set_date_format_command(message: Message):
            if not await self._ensure_owner_message(message):
                return
            await self.settings_handlers.handle_set_date_format_command(message)

        @self.dp.callback_query()
        async def handle_callbacks(callback: CallbackQuery):
            if not await self._ensure_owner_callback(callback):
                return
            await self.callback_handlers.handle_callback(callback)

    async def _ensure_owner_message(self, message: Message) -> bool:
        user = getattr(message, "from_user", None)
        user_id = getattr(user, "id", None)
        if user_id is not None and is_owner(user_id):
            return True

        logger.warning("Blocked command from non-owner user %s", user_id)
        await message.answer("🚫 Этот бот доступен только владельцу.")
        return False

    async def _ensure_owner_callback(self, callback: CallbackQuery) -> bool:
        user = getattr(callback, "from_user", None)
        user_id = getattr(user, "id", None)
        if user_id is not None and is_owner(user_id):
            return True

        logger.warning("Blocked callback from non-owner user %s", user_id)
        await callback.answer("🚫 У вас нет доступа к этому боту", show_alert=True)
        return False
