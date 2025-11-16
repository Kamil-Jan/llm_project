from ..utils.logger import setup_logger
from .service import Service

logger = setup_logger(__name__)


class SchedulerService(Service):
    def __init__(self):
        super().__init__(logger)

    async def parse_event_command(self, command_text: str) -> dict:
        return None
