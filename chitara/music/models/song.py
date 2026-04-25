from django.contrib.auth.models import User
from django.db import models

from .generation_status import GenerationStatus


class Song(models.Model):
    title             = models.CharField(max_length=255)
    user              = models.ForeignKey(User, on_delete=models.CASCADE, related_name='songs')
    singer_model      = models.ForeignKey('music.SingerModel', on_delete=models.PROTECT)
    genre             = models.ForeignKey('music.Genre', on_delete=models.PROTECT)
    mood              = models.ForeignKey('music.Mood', on_delete=models.PROTECT)
    occasion          = models.ForeignKey('music.Occasion', on_delete=models.PROTECT)
    themes            = models.ManyToManyField('music.Theme', blank=True)
    review_notes      = models.TextField()
    duration          = models.PositiveIntegerField(help_text='Duration in seconds')
    generation_status = models.CharField(
        max_length=20,
        choices=GenerationStatus.choices,
        default=GenerationStatus.PENDING,
    )
    audio_url   = models.URLField(blank=True, default='')
    image_url   = models.URLField(blank=True, default='')
    external_id = models.CharField(max_length=255, blank=True, default='')
    is_shared   = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
