import asyncio
import sys
import signal
from functools import partial
from typing import Optional, List

from .utils.logger import setup_logger
from .bot.service import TelegramBot
from .userbot.service import UserBot
from .config.settings import settings
from .config.database import init_db, close_db
from .services.service import Service
from .services.ai_service import AiService
from .services.search_service import SearchService
from .services.event_service import EventService
from .services.scheduler_service import SchedulerService
from .services.user_settings_service import UserSettingsService
from .services.calendar_service import CalendarService
from .utils.exceptions import BaseError

logger = setup_logger(__name__)


class Application:
    def __init__(self):
        self.scheduler_service: Optional[SchedulerService] = None
        self.calendar_service: Optional[CalendarService] = None
        self.ai_service: Optional[AiService] = None
        self.bot: Optional[TelegramBot] = None
        self.user_bot: Optional[UserBot] = None
        self.services: List[Service] = []

    async def initialize_services(self):
        try:
            logger.info("Initializing application services...")

            logger.info("Initializing database...")
            await init_db()

            self.scheduler_service = SchedulerService()
            self.services.append(self.scheduler_service)

            self.calendar_service = CalendarService()
            self.services.append(self.calendar_service)

            self.user_settings_service = UserSettingsService()
            self.services.append(self.user_settings_service)

            self.search_service = SearchService()
            self.services.append(self.search_service)

            self.ai_service = AiService(
                search_service=self.search_service,
                user_settings_service=self.user_settings_service
            )
            self.services.append(self.ai_service)

            self.event_service = EventService(
                user_settings_service=self.user_settings_service
            )
            self.services.append(self.event_service)

            self.user_bot = UserBot(
                ai_service=self.ai_service,
                event_service=self.event_service,
                user_settings_service=self.user_settings_service
            )
            self.services.append(self.user_bot)

            # bot should be last
            self.bot = TelegramBot(
                user_settings_service=self.user_settings_service,
                event_service=self.event_service,
            )
            self.services.append(self.bot)

            for service in self.services:
                await service.initialize()

            logger.info("All services successfuly initiated")

        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise BaseError(f"Failed to initialize services: {e}")

    async def start_services(self):
        try:
            logger.info("Starting telegram bot services...")

            for service in self.services:
                await service.start()

        except Exception as e:
            logger.error(f"Failed to start services: {e}")
            raise BaseError(f"Failed to start services: {e}")


    async def stop_services(self):
        logger.info("Performing cleanup and stopping services...")

        for service in self.services[::-1]:
            try:
                await service.stop()
            except Exception as e:
                logger.error(f"Failed to stop service: {e}")

        try:
            await close_db()
            logger.info("Database is closed")
        except Exception as e:
            logger.error(f"Failed to close database: {e}")

        logger.info("All services are stopped")


async def main():
    logger.info("Starting telegram bot...")
    logger.info(f"Log level: {settings.log_level}")

    try:
        app = Application()
        await app.initialize_services()

        await app.start_services()
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
    finally:
        await app.stop_services()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        logger.info("Application shutdown complete")
