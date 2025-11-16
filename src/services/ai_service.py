from ..config.settings import settings
from ..utils.logger import setup_logger
from .service import Service
from datetime import datetime

logger = setup_logger(__name__)


class AiService(Service):
    def __init__(self):
        super().__init__(logger)

    async def parse_event_command(self, command_text: str) -> dict:
        return {
            'event_name': 'My Event',
            'description': 'Description',
            'event_datetime': datetime(2025, 11, 16, 20, 0, 0),
            'end_datetime': datetime(2025, 11, 16, 20, 0, 0),
            'reminder_times': [15, 60],
            'timezone': settings.timezone
        }
