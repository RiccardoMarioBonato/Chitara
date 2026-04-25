import logging

from .base import SongGeneratorStrategy

logger = logging.getLogger(__name__)

MOCK_AUDIO_URL = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
MOCK_IMAGE_URL = "https://picsum.photos/seed/chitara-mock/400/400"
MOCK_DURATION_SECONDS = 229


class MockSongGeneratorStrategy(SongGeneratorStrategy):

    def generate(self, song_request) -> dict:
        if isinstance(song_request, dict):
            title = song_request.get("title", "Mock Song")
            prompt = song_request.get("prompt", "")
        else:
            title = getattr(song_request, "title", "Mock Song")
            prompt = getattr(song_request, "prompt", "")

        logger.info("MockStrategy: generating for title=%r", title)

        return {
            "status": "SUCCESS",
            "audio_url": MOCK_AUDIO_URL,
            "image_url": MOCK_IMAGE_URL,
            "task_id": "",
            "duration_seconds": MOCK_DURATION_SECONDS,
        }
