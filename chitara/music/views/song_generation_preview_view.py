import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import QueryDict
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View

from ..forms import SongGenerationForm
from ..services import InvalidGenerationInput, SongGenerationError, SongGenerationService

logger = logging.getLogger(__name__)


class SongGenerationPreviewView(LoginRequiredMixin, View):
    template_name = 'music/song_preview.html'

    def _get_form_from_session(self, request):
        stored = request.session.get('song_preview_data')
        if not stored:
            return None, None
        qd = QueryDict('', mutable=True)
        for key, values in stored.items():
            qd.setlist(key, values)
        form = SongGenerationForm(data=qd)
        form.is_valid()
        return form, stored

    def get(self, request):
        form, stored = self._get_form_from_session(request)
        if form is None:
            return redirect(reverse_lazy('music:song-generate'))
        return render(request, self.template_name, {'form': form, 'preview': form.cleaned_data})

    def post(self, request):
        form, stored = self._get_form_from_session(request)
        if form is None:
            messages.error(request, 'Session expired. Please fill in the form again.')
            return redirect(reverse_lazy('music:song-generate'))

        if not form.is_valid():
            request.session.pop('song_preview_data', None)
            messages.error(request, 'Preview data was invalid. Please try again.')
            return redirect(reverse_lazy('music:song-generate'))

        service = SongGenerationService()
        try:
            song = service.generate_song(user=request.user, form_data=form.cleaned_data)
        except InvalidGenerationInput as exc:
            logger.warning('Invalid preview input from user %s: %s', request.user.pk, exc)
            messages.error(request, str(exc))
            return redirect(reverse_lazy('music:song-generate'))
        except SongGenerationError:
            logger.error('Generation error for user %s', request.user.pk)
            messages.error(request, 'Song generation failed. Please try again later.')
            return redirect(reverse_lazy('music:song-generate'))

        request.session.pop('song_preview_data', None)
        messages.success(request, f'"{song.title}" has been submitted for generation!')
        return redirect(reverse_lazy('music:song-detail', kwargs={'pk': song.pk}))
