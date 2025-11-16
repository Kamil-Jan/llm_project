from tortoise import Tortoise

from .settings import settings
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


TORTOISE_ORM = {
    "connections": {"default": settings.database_url},
    "apps": {
        "models": {
            "models": ["src.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}

async def init_db():
    try:
        logger.info("Initializing database connection...")

        await Tortoise.init(
            db_url=settings.database_url,
            modules={"models": ["src.models"]},
        )

        logger.info("Database initialized successfully")
        await Tortoise.generate_schemas()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_db():
    try:
        logger.info("Closing database connections...")
        await Tortoise.close_connections()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")
