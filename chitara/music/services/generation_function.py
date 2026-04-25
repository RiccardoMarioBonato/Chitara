from ..strategies.factory import StrategyFactory


def generate_song(song_request, force_mock=False, song_instance=None):
    strategy = StrategyFactory.get_strategy(force_mock=force_mock)
    if hasattr(strategy, '_poll_until_done') and song_instance is not None:
        return strategy.generate(song_request, song_instance=song_instance)
    return strategy.generate(song_request)
