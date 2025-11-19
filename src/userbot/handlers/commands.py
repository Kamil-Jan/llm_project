import asyncio
from pyrogram.types import Message
from pyrogram.enums import ParseMode

from ...services.ai_service import AiService
from ...services.event_service import EventService
from ...services.user_settings_service import UserSettingsService
from ...utils.logger import setup_logger
from ...utils.helpers import is_owner, extract_chat_info
from ...utils.exceptions import DateParsingError, EventError
from ..message_manager import MessageManager

logger = setup_logger(__name__)


class CommandHandlers:
    def __init__(
        self,
        ai_service: AiService,
        event_service: EventService,
        user_settings_service: UserSettingsService,
        message_manager: MessageManager
    ):
        self.ai_service = ai_service
        self.event_service = event_service
        self.user_settings_service = user_settings_service
        self.message_manager = message_manager

    async def handle_help_command(self, message: Message) -> None:
        try:
            chat_id, chat_title, chat_type = extract_chat_info(message.chat)

            await self.message_manager.create_help_message(message)

            try:
                await message.delete()
            except Exception as e:
                logger.warning(f"Could not delete help command message: {e}")

            logger.info(f"Sent help message to chat {chat_id}")

        except Exception as e:
            logger.error(f"Error handling help command: {e}")
            await self.message_manager.create_error_message(message, "ERROR: Произошла ошибка при отображении справки")

    async def _process_event_text(self, message: Message, raw_text: str) -> None:
        try:
            chat_id, chat_title, chat_type = extract_chat_info(message.chat)

            is_owner_user = is_owner(message.from_user.id)
            is_private_chat = chat_id > 0

            if not is_owner_user:
                if not is_private_chat:
                    logger.warning(
                        f"Non-owner {message.from_user.id} tried to create event in non-private chat {chat_id}"
                    )
                    return
                logger.info(
                    f"Processing ++event command from non-owner user {message.from_user.id} in private chat {chat_id}"
                )
            else:
                logger.info(f"Processing ++event command from owner {message.from_user.id}")

            if chat_type not in ['private', 'group', 'supergroup']:
                logger.warning(f"Event creation attempted in unsupported chat type: {chat_type}")
                return

            ####### AI MODEL PARSING #######
            try:
                logger.info(f"Original event text: '{raw_text}'")
                event_data = await self.ai_service.parse_event_command(raw_text)
            except DateParsingError as e:
                await self.message_manager.create_error_message(
                    message,
                    f"Could not parse event: {e}"
                )
                return
            ################################

            if event_data is None:
                logger.info("AiService returned no event_data (not an event) — skipping")
                return

            if event_data.get('result') == 'BAD' or event_data.get('message') is None:
                await self.message_manager.create_answer(
                    message,
                    event_data.get('message', 'Лучше не создавать событие в это время')
                )
                return

            try:
                event = await self.event_service.create_event(
                    chat_id=chat_id,
                    user_id=message.from_user.id,
                    event_data=event_data
                )
            except EventError as e:
                await self.message_manager.create_error_message(
                    message,
                    f"Could not create event: {e}"
                )
                return

            #try:
            #    await message.delete()
            #except Exception as e:
            #    logger.warning(f"Could not delete event command message: {e}")

            pinned_event_text = self.event_service.generate_pinned_event_message(event)

            message_id = await self.message_manager.create_and_pin_event_message(
                chat_id=chat_id,
                event_text=pinned_event_text,
                event=event
            )
            if message_id:
                event.message_id = message_id
                await event.save(update_fields=['message_id'])

                creator_info = "owner" if is_owner(message.from_user.id) else f"user {message.from_user.id}"
                logger.info(
                    f"Created event '{event.event_name}' in chat {chat_id} by {creator_info}"
                )
                if event_data.get('message'):
                    try:
                        await self.message_manager.create_answer(
                            message,
                            event_data['message']
                        )
                    except Exception as e:
                        logger.warning(f"Could not send LLM explanation for good event: {e}")
            else:
                logger.error("Failed to create event message")
                await event.delete()

        except Exception as e:
            logger.error(f"Error processing event text: {e}")
            await self.message_manager.create_error_message(
                message,
                "ERROR: Произошла ошибка при создании события"
            )


    async def handle_event_command(self, message: Message) -> None:
        """Обработчик текстовой команды ++event ..."""
        if not message.text:
            return
        await self._process_event_text(message, message.text)
