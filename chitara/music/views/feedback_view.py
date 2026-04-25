from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView

from ..models import Feedback


class FeedbackView(LoginRequiredMixin, CreateView):
    model = Feedback
    fields = ['content']
    template_name = 'music/feedback.html'
    success_url = reverse_lazy('music:song-library')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Thank you for your feedback!')
        return super().form_valid(form)
