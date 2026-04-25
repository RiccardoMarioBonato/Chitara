import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chitara.settings")
django.setup()

from music.strategies.factory import StrategyFactory
from music.strategies.mock_strategy import MockSongGeneratorStrategy
from music.strategies.suno_strategy import SunoSongGeneratorStrategy
from music.strategies.base import SongGeneratorStrategy
from music.strategies.exceptions import SunoOfflineError, SunoInsufficientCreditsError

SAMPLE_REQUEST = {
    "prompt": "A calm lo-fi instrumental with soft piano and rain sounds",
    "title": "Rainy Study Session",
    "genre": "Lo-fi",
    "mood": "Calm",
    "duration": 30,
}

SEP = "-" * 60


def demo_mock():
    print(SEP)
    print("Mock Strategy")
    print(SEP)

    strategy = MockSongGeneratorStrategy()
    assert isinstance(strategy, SongGeneratorStrategy)

    print(f"  Strategy : {strategy.__class__.__name__}")
    print(f"  Is base  : {isinstance(strategy, SongGeneratorStrategy)}")

    result = strategy.generate(SAMPLE_REQUEST)
    print(f"  Status   : {result['status']}")
    print(f"  Audio URL: {result['audio_url']}")
    print(f"  Duration : {result['duration_seconds']}s")

    assert result["status"] == "SUCCESS"
    assert result["audio_url"]
    print("  [PASS]\n")


def demo_factory_mock():
    print(SEP)
    print("Factory -> Mock")
    print(SEP)
    from django.conf import settings
    original = getattr(settings, "GENERATOR_STRATEGY", "mock")
    settings.GENERATOR_STRATEGY = "mock"

    strategy = StrategyFactory.get_strategy()
    print(f"  Returned : {strategy.__class__.__name__}")
    assert isinstance(strategy, MockSongGeneratorStrategy)

    result = strategy.generate(SAMPLE_REQUEST)
    assert result["status"] == "SUCCESS"
    print("  [PASS]\n")

    settings.GENERATOR_STRATEGY = original


def demo_factory_suno():
    print(SEP)
    print("Factory -> Suno")
    print(SEP)
    from django.conf import settings
    original = getattr(settings, "GENERATOR_STRATEGY", "mock")
    settings.GENERATOR_STRATEGY = "suno"

    strategy = StrategyFactory.get_strategy()
    print(f"  Returned : {strategy.__class__.__name__}")
    assert isinstance(strategy, SunoSongGeneratorStrategy)
    assert isinstance(strategy, SongGeneratorStrategy)

    print(f"  Is base  : True")
    print(f"  API key  : {'set' if strategy.api_key else 'not set'}")
    print("  [PASS]\n")

    settings.GENERATOR_STRATEGY = original


def demo_suno_live():
    print(SEP)
    print("Suno Strategy - Live API call")
    print(SEP)
    from django.conf import settings
    api_key = getattr(settings, "SUNO_API_KEY", "")

    if not api_key or api_key == "your_suno_api_key_here":
        print("  SUNO_API_KEY not set, skipping live test.\n")
        return

    strategy = SunoSongGeneratorStrategy()
    print(f"  Strategy : {strategy.__class__.__name__}")

    try:
        result = strategy.generate(SAMPLE_REQUEST)
        print(f"  Status   : {result['status']}")
        print(f"  Task ID  : {result['task_id']}")
        assert result["status"] == "PENDING"
        assert result["task_id"]
        print("  [PASS]\n")

        import time
        print("  Polling (6s)...")
        time.sleep(6)
        poll_data = strategy._poll_status(result["task_id"])
        clip = strategy._extract_clip(poll_data)
        if clip:
            print(f"  Poll status: {clip['status']}")
        else:
            print("  Still processing...")
        print("  [PASS]\n")

    except SunoOfflineError as exc:
        print(f"  Suno offline: {exc}\n")
    except SunoInsufficientCreditsError as exc:
        print(f"  Insufficient credits: {exc}\n")
    except Exception as exc:
        print(f"  Error: {exc}\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  Chitara Strategy Demo")
    print("=" * 60 + "\n")

    demo_mock()
    demo_factory_mock()
    demo_factory_suno()
    demo_suno_live()

    print(SEP)
    print("Done.")
    print(SEP + "\n")
