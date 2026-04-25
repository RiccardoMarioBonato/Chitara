import logging

from django.conf import settings

from .mock_strategy import MockSongGeneratorStrategy
from .suno_strategy import SunoSongGeneratorStrategy

logger = logging.getLogger(__name__)

STRATEGY_REGISTRY = {
    "mock": MockSongGeneratorStrategy,
    "suno": SunoSongGeneratorStrategy,
}


class StrategyFactory:

    @staticmethod
    def get_strategy(force_mock: bool = False):
        if force_mock:
            return MockSongGeneratorStrategy()

        strategy_name = getattr(settings, "GENERATOR_STRATEGY", "mock").lower().strip()

        # Force mock when no API key is configured — prevents accidental Suno calls
        if not getattr(settings, "SUNO_API_KEY", ""):
            strategy_name = "mock"

        strategy_class = STRATEGY_REGISTRY.get(strategy_name)

        if strategy_class is None:
            logger.warning("Unknown GENERATOR_STRATEGY %r, falling back to mock.", strategy_name)
            strategy_class = MockSongGeneratorStrategy

        logger.info("Using strategy: %s", strategy_class.__name__)
        return strategy_class()
