from ..utils.logger import setup_logger
from .service import Service

logger = setup_logger(__name__)


class CalendarService(Service):
    def __init__(self):
        super().__init__(logger)
