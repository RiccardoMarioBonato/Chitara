from django.db import models


class GenerationStatus(models.TextChoices):
    PENDING    = 'PENDING',    'Pending'
    GENERATING = 'GENERATING', 'Generating'
    COMPLETED  = 'COMPLETED',  'Completed'
    FAILED     = 'FAILED',     'Failed'
