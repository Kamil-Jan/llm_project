from pathlib import Path
from deepgram import AsyncDeepgramClient

from ..config.settings import settings
from ..services.service import Service
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class AsrService(Service):
    def __init__(self):
        super().__init__(logger)
        self._client = AsyncDeepgramClient(api_key=settings.deepgram_api_key)

    async def initialize(self):
        pass

    async def start(self):
        pass

    async def stop(self):
        pass

    async def transcribe_file(self, path: Path) -> str:
        audio_bytes = path.read_bytes()

        response = await self._client.listen.v1.media.transcribe_file(
            request=audio_bytes,
            model="nova-3",
            smart_format=True,
            language="ru",
        )

        try:
            return (
                response.results.channels[0]
                .alternatives[0]
                .transcript
            ).strip()
        except Exception as e:
            logger.error(f"ASR transcription error: {e}")
            return ""
