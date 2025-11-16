from typing import Optional
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

from ..services.service import Service
from ..config.settings import settings
from ..utils.logger import setup_logger
from ..utils.exceptions import TelegramError
from .handlers.settings import SettingsHandlers
from .handlers.events import EventHandlers
from .handlers.callbacks import CallbackHandlers


logger = setup_logger(__name__)


class TelegramBot(Service):
    def __init__(self):
        super().__init__(logger)

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

            self.event_handlers = EventHandlers()

            self.settings_handlers = SettingsHandlers()

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
            await self.event_handlers.handle_start(message, message.from_user, to_answer=True)

        @self.dp.callback_query(F.data.startswith("main_menu"))
        async def settings_callback(callback: CallbackQuery):
            await callback.answer()
            await self.event_handlers.handle_start(callback.message, callback.from_user, to_answer=False)

        @self.dp.message(Command("help"))
        async def start_command(message: Message):
            await self.event_handlers.handle_help(message, message.from_user, to_answer=True)

        @self.dp.callback_query(F.data.startswith("help"))
        async def settings_callback(callback: CallbackQuery):
            await callback.answer()
            await self.event_handlers.handle_help(callback.message, callback.from_user, to_answer=False)

        @self.dp.message(Command("settings"))
        async def settings_command(message: Message):
            """Handle /settings command."""
            await self.settings_handlers.handle_settings_menu(message)

        @self.dp.callback_query(F.data.startswith("settings"))
        async def settings_callback(callback: CallbackQuery):
            """Handle settings button."""
            await self.settings_handlers.handle_settings_callback(callback)

        @self.dp.callback_query()
        async def handle_callbacks(callback: CallbackQuery):
            """Handle all callback queries."""
            await self.callback_handlers.handle_callback(callback)
