from django.db.models import Q
from django.views.generic import ListView

from ..models import Song


class SharedSongListView(ListView):
    model = Song
    template_name = 'music/shared_song_list.html'
    context_object_name = 'songs'
    paginate_by = 20

    def get_queryset(self):
        qs = Song.objects.filter(is_shared=True, generation_status='COMPLETED').select_related(
            'genre', 'mood', 'singer_model'
        )
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(title__icontains=q))
        sort = self.request.GET.get('sort', 'newest')
        if sort == 'oldest':
            qs = qs.order_by('created_at')
        elif sort == 'title':
            qs = qs.order_by('title')
        else:
            qs = qs.order_by('-created_at')
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_q'] = self.request.GET.get('q', '')
        ctx['current_sort'] = self.request.GET.get('sort', 'newest')
        ctx['total_shared'] = Song.objects.filter(is_shared=True, generation_status='COMPLETED').count()
        return ctx
