from typing import Optional
from pyrogram import Client, filters
from pyrogram.types import Message

from ..config.settings import settings
from ..services.service import Service
from ..services.ai_service import AiService
from ..services.event_service import EventService
from ..utils.exceptions import TelegramError
from ..utils.logger import setup_logger
from ..utils.helpers import is_owner
from .handlers.commands import CommandHandlers
from .message_manager import MessageManager

logger = setup_logger(__name__)


class UserBot(Service):
    def __init__(self, ai_service: AiService, event_service: EventService):
        super().__init__(logger)

        self.ai_service = ai_service
        self.event_service = event_service

        self.client: Optional[Client] = None
        self.message_manager: Optional[MessageManager]
        self.command_handlers: Optional[CommandHandlers]
        self._running = False

    async def initialize(self):
        await super().initialize()

        try:
            self.client = Client(
                name="project_userbot",
                api_id=settings.telegram_api_id,
                api_hash=settings.telegram_api_hash,
                phone_number=settings.telegram_phone_number,
                workdir="./sessions"
            )

            self.message_manager = MessageManager(
                client=self.client,
            )

            self.command_handlers = CommandHandlers(
                ai_service=self.ai_service,
                event_service=self.event_service,
                message_manager=self.message_manager,
            )

            self._setup_handlers()

            logger.info("UserBot initialized")
        except Exception as e:
            logger.error(f"Failed to initialize UserBot: {e}")
            raise TelegramError(f"UserBot initialization failed: {e}")

    async def start(self):
        await super().start()

        if self._running:
            logger.warning("UserBot is already running")
            return

        try:
            if not self.client:
                await self.initialize()

            await self.client.start()
            self._running = True

            me = await self.client.get_me()
            logger.info(f"UserBot started as {me.first_name} (@{me.username})")

        except Exception as e:
            logger.error(f"Failed to start user bot: {e}")
            raise TelegramError(f"UserBot start failed: {e}")

    async def stop(self):
        await super().stop()

        if not self._running:
            logger.warning("UserBot is not running...")
            return

        try:
            await self.client.stop()

            self._running = False
            logger.info("User bot stopped")

        except Exception as e:
            logger.error(f"Error stopping bot: {e}")

    def _setup_handlers(self):
        @self.client.on_message(filters.text & filters.me)
        async def handle_my_messages(client: Client, message: Message):
            try:
                if not is_owner(message.from_user.id):
                    return

                text = message.text.strip()

                if text.startswith('++help'):
                    await self.command_handlers.handle_help_command(message)
                elif text.startswith('++event'):
                    logger.info("Got event command")
                    await self.command_handlers.handle_event_command(message)

            except Exception as e:
                logger.error(f"Error handling message: {e}")

        @self.client.on_message(filters.text & ~filters.me)
        async def handle_other_messages(client: Client, message: Message):
            """Handle messages from others (for monitoring purposes)."""
            try:
                if message.chat.id > 0:
                    text = message.text.strip()

                    if text.startswith('++help'):
                        logger.info(f"Received ++help command from user {message.from_user.id} in private chat")
                        await self.command_handlers.handle_help_command(message)
                    elif text.startswith('++event'):
                        logger.info(f"Received ++event command from user {message.from_user.id} in private chat")
                        await self.command_handlers.handle_event_command(message)

            except Exception as e:
                logger.error(f"Error handling other user message: {e}")
