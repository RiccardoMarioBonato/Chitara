from abc import ABC, abstractmethod


class SongGeneratorStrategy(ABC):

    @abstractmethod
    def generate(self, song_request) -> dict:
        raise NotImplementedError(f"{self.__class__.__name__} must implement generate()")

    def __repr__(self):
        return f"<{self.__class__.__name__}>"
