import asyncio
from typing import Optional, Dict, Any
from pyrogram import Client
from pyrogram.types import Message
from pyrogram.enums import ParseMode

from ..models import Event
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class MessageManager:
    def __init__(self, client: Client):
        self.client = client

    async def create_and_pin_event_message(
        self,
        chat_id: int,
        event_text: str,
        event: Event
    ) -> Optional[int]:
        try:
            message = await self.client.send_message(
                chat_id=chat_id,
                text=event_text
            )

            if not message:
                return None

            # TODO ??? Cache message info
            #self._cache_message_info(message.id, chat_id, datetime.utcnow())

            # Try to pin the message
            try:
                # Check if this is a private chat (positive chat_id indicates private chat)
                is_private_chat = chat_id > 0

                if is_private_chat:
                    # For private chats, use both_sides=True so both participants see the pin
                    await self.client.pin_chat_message(
                        chat_id=chat_id,
                        message_id=message.id,
                        disable_notification=False,  # Notify about pinning
                        both_sides=True  # Pin for both participants in private chat
                    )
                else:
                    # For group chats, both_sides parameter is not applicable
                    await self.client.pin_chat_message(
                        chat_id=chat_id,
                        message_id=message.id,
                        disable_notification=False  # Notify all users when pinning
                    )

                logger.info(f"Pinned event message {message.id} in chat {chat_id} (private: {is_private_chat})")
            except Exception as e:
                logger.warning(f"Could not pin message {message.id}: {e}")

            return message.id

        except Exception as e:
            logger.error(f"Failed to create event message: {e}")
            return None

    async def create_help_message(self, message: Message):
        help_text = """
🕐 **Как использовать команду ++event**
> Она нужна, если нужно поставить мне дедлайн или назначить со мной встречу так чтобы я о ней не забыл.

Просто напиши ++event и опиши событие любым способом:

**Примеры:**
• `++event Дедлайн: доделать мипт тех через неделю`
• `++event встреча по продукту в среду в 13:30 на час`
• `++event стоматолог 25 августа в 10:00`
• `++event созвон с командой через 2 часа`
• `++event день рождения друга в пятницу весь день`

**Напоминания** можно указывать явно:
• `--remind 15m`
• `--remind 15,1h,2h,1d,2d`
•  можно не указывать вообще, тогда они будут взяты по умолчанию

**Пример:**
• `++event встреча с коллегами завтра в 15:00 --remind 1h,2h`


Все события автоматически синхронизируются с моим Apple календарем.
"""
        await self._send_reply(message, help_text, 300)

    async def create_error_message(self, message: Message, error_text: str):
        await self._send_reply(message, error_text, 10)

    async def _send_reply(self, message: Message, reply_text: str, delete_delay_seconds: int) -> None:
        try:
            reply = await message.reply(reply_text, parse_mode=ParseMode.MARKDOWN)
            if reply:
                asyncio.create_task(self._delete_message_after_delay(reply, delete_delay_seconds))
        except Exception as e:
            logger.error(f"Failed to send error reply: {e}")

    async def _delete_message_after_delay(self, message: Message, delay_seconds: int) -> None:
        try:
            await asyncio.sleep(delay_seconds)
            await message.delete()
        except Exception as e:
            logger.debug(f"Could not delete message after delay: {e}")
