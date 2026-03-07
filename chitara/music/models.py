from django.db import models


class Genre(models.TextChoices):
    JAZZ = 'JAZZ', 'Jazz'
    POP = 'POP', 'Pop'
    ELECTRONIC = 'ELECTRONIC', 'Electronic'
    CLASSICAL = 'CLASSICAL', 'Classical'
    ROCK = 'ROCK', 'Rock'
    HIPHOP = 'HIPHOP', 'Hip Hop'


class Mood(models.TextChoices):
    CALM = 'CALM', 'Calm'
    HAPPY = 'HAPPY', 'Happy'
    ENERGETIC = 'ENERGETIC', 'Energetic'
    ROMANTIC = 'ROMANTIC', 'Romantic'
    SAD = 'SAD', 'Sad'


class Occasion(models.TextChoices):
    BIRTHDAY = 'BIRTHDAY', 'Birthday'
    WEDDING = 'WEDDING', 'Wedding'
    GRADUATION = 'GRADUATION', 'Graduation'
    HOLIDAY = 'HOLIDAY', 'Holiday'
    CASUAL = 'CASUAL', 'Casual'


class Theme(models.TextChoices):
    CHRISTMAS = 'CHRISTMAS', 'Christmas'
    HALLOWEEN = 'HALLOWEEN', 'Halloween'
    LOVE = 'LOVE', 'Love'
    SUMMER = 'SUMMER', 'Summer'
    MAGICAL = 'MAGICAL', 'Magical'


class GenerationStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    GENERATING = 'GENERATING', 'Generating'
    COMPLETED = 'COMPLETED', 'Completed'
    FAILED = 'FAILED', 'Failed'


class User(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class SingerModel(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Song(models.Model):
    title = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='songs')
    singer_model = models.ForeignKey(SingerModel, on_delete=models.PROTECT)
    genre = models.CharField(max_length=20, choices=Genre.choices)
    mood = models.CharField(max_length=20, choices=Mood.choices)
    occasion = models.CharField(max_length=20, choices=Occasion.choices)
    themes = models.JSONField(default=list, blank=True)
    review_notes = models.TextField()
    duration = models.PositiveIntegerField(help_text='Duration in seconds')
    generation_status = models.CharField(
        max_length=20,
        choices=GenerationStatus.choices,
        default=GenerationStatus.PENDING
    )
    is_shared = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks')
    content = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Feedback by {self.user.name} at {self.submitted_at}'