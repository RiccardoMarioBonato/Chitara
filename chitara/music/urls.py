"""
URL Configuration — music/urls.py

Include in the project's root urls.py with:
    path('songs/', include('music.urls', namespace='music')),
"""

from django.urls import path

from .views import FeedbackView, SongDetailView, SongGenerationView, SongLibraryView, SunoCallbackView, get_song_status

app_name = 'music'

urlpatterns = [
    # Song generation form + submission
    path('generate/',        SongGenerationView.as_view(),  name='song-generate'),

    # Paginated library / list view
    path('',                 SongLibraryView.as_view(),     name='song-library'),

    # Individual song detail (owner-only)
    path('<int:pk>/',        SongDetailView.as_view(),      name='song-detail'),

    # User feedback form
    path('feedback/',        FeedbackView.as_view(),        name='feedback'),

    # Suno AI webhook — receives POST when audio is ready
    # Full URL: /songs/api/callback/
    path('api/callback/',    SunoCallbackView.as_view(),    name='suno-callback'),

    # Strategy polling endpoint — frontend polls this to check generation status
    path('generation/status/<int:song_id>/', get_song_status, name='song-status'),
]
