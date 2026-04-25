from django.apps import AppConfig


class MusicConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'music'

    def ready(self):
        from django.db.models.signals import post_migrate
        post_migrate.connect(_seed_lookup_data, sender=self)


def _seed_lookup_data(sender, **kwargs):
    from music.models import Genre, Mood, Occasion, Theme, SingerModel

    for name in ['Pop', 'Rock', 'Jazz', 'Classical', 'Hip-Hop']:
        Genre.objects.get_or_create(name=name)

    for name in ['Happy', 'Energetic', 'Calm', 'Melancholic', 'Romantic']:
        Mood.objects.get_or_create(name=name)

    for name in ['Party', 'Wedding', 'Workout', 'Study', 'Relaxation']:
        Occasion.objects.get_or_create(name=name)

    for name in ['Summer', 'Love', 'Adventure', 'Nostalgia', 'Nature']:
        Theme.objects.get_or_create(name=name)

    for name, desc in [
        ('Soprano',  'High female vocal range'),
        ('Alto',     'Low female vocal range'),
        ('Tenor',    'High male vocal range'),
        ('Baritone', 'Medium male vocal range'),
        ('Bass',     'Low male vocal range'),
    ]:
        SingerModel.objects.get_or_create(name=name, defaults={'description': desc})
