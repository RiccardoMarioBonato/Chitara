from django.contrib.auth.models import User
from django.db import models


class Feedback(models.Model):
    user         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks')
    content      = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Feedback by {self.user.username} at {self.submitted_at}'
