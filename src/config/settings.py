from typing import List

from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    telegram_api_id: str
    telegram_api_hash: str
    telegram_phone_number: str
    telegram_bot_token: str
    owner_user_id: int

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    timezone: str = "UTC"
    default_reminder_times: str = "15m,1h"

    log_level: str = "INFO"

    yandex_folder_id: str = ""
    yandex_api_key: str = ""

    openai_api_key: str = ""

    @validator("default_reminder_times")
    def parse_reminder_times(cls, v: str) -> List[str]:
        """Parse comma-separated reminder times."""
        return [time.strip() for time in v.split(",") if time.strip()]

    @property
    def database_url(self) -> str:
        """Generate database URL for TortoiseORM."""
        return (
            f"asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
