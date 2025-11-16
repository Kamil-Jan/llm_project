from aiogram.types import CallbackQuery, Message
from ...utils.logger import setup_logger
from ..keyboards import KeyboardBuilder

logger = setup_logger(__name__)


class CallbackHandlers:
    def __init__(self):
        pass

    async def handle_callback(self, callback: CallbackQuery) -> None:
        try:
            data = callback.data
            logger.info(f"Received callback: {data} from user {callback.from_user.id}")
            await callback.answer()
            logger.warning(f"Unhandled callback data: {data}")
            await callback.message.answer("⚠️ Эта функция еще не реализована.")

        except Exception as e:
            logger.error(f"Error handling callback: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
