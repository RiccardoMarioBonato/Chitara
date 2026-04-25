from .feedback_admin import FeedbackAdmin
from .genre_admin import GenreAdmin
from .mood_admin import MoodAdmin
from .occasion_admin import OccasionAdmin
from .singer_model_admin import SingerModelAdmin
from .song_admin import SongAdmin
from .theme_admin import ThemeAdmin

__all__ = [
    'GenreAdmin', 'MoodAdmin', 'OccasionAdmin', 'ThemeAdmin',
    'SingerModelAdmin', 'SongAdmin', 'FeedbackAdmin',
]
