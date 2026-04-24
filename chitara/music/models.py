from django.db import models
from django.contrib.auth.models import User

class GenerationStatus(models.TextChoices):
    PENDING    = 'PENDING',    'Pending'
    GENERATING = 'GENERATING', 'Generating'
    COMPLETED  = 'COMPLETED',  'Completed'
    FAILED     = 'FAILED',     'Failed'

class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Mood(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Occasion(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Theme(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class SingerModel(models.Model):
    name        = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Song(models.Model):
    title             = models.CharField(max_length=255)
    user              = models.ForeignKey(User, on_delete=models.CASCADE, related_name='songs')
    singer_model      = models.ForeignKey(SingerModel, on_delete=models.PROTECT)
    genre             = models.ForeignKey(Genre, on_delete=models.PROTECT)
    mood              = models.ForeignKey(Mood, on_delete=models.PROTECT)
    occasion          = models.ForeignKey(Occasion, on_delete=models.PROTECT)
    themes            = models.ManyToManyField(Theme, blank=True)
    review_notes      = models.TextField()
    duration          = models.PositiveIntegerField(help_text='Duration in seconds')
    generation_status = models.CharField(
        max_length=20,
        choices=GenerationStatus.choices,
        default=GenerationStatus.PENDING
    )
    audio_url   = models.URLField(blank=True, default='')
    image_url   = models.URLField(blank=True, default='')
    external_id = models.CharField(max_length=255, blank=True, default='')
    is_shared   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Feedback(models.Model):
    user         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks')
    content      = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Feedback by {self.user.username} at {self.submitted_at}'