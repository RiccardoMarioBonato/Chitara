import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chitara.settings')
django.setup()

from music.models import Genre, Mood, Occasion, Theme

# Create Genres
genres = ['Pop', 'Rock', 'Jazz', 'Classical', 'Electronic', 'Hip-Hop', 'R&B', 'Country']
for genre in genres:
    Genre.objects.get_or_create(name=genre)

# Create Moods
moods = ['Happy', 'Sad', 'Energetic', 'Calm', 'Romantic', 'Aggressive', 'Mysterious']
for mood in moods:
    Mood.objects.get_or_create(name=mood)

# Create Occasions
occasions = ['Party', 'Wedding', 'Workout', 'Sleep', 'Study', 'Dinner', 'Celebration']
for occasion in occasions:
    Occasion.objects.get_or_create(name=occasion)

# Create Themes
themes = ['Summer', 'Love', 'Nature', 'Urban', 'Fantasy', 'Adventure', 'Nostalgia']
for theme in themes:
    Theme.objects.get_or_create(name=theme)

print("Sample data created.")