"""
User Story Tests — Chitara SRS v1.0
Tests all 14 user stories using the Mock generation strategy.
No external API calls are made.

Run with:
    python manage.py test music.tests.test_user_stories -v 2
"""

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chitara.settings')

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from music.models import GenerationStatus, Genre, Mood, Occasion, SingerModel, Song, Theme

MOCK_SETTINGS = {'GENERATOR_STRATEGY': 'mock'}


def make_user(username='testuser', password='testpass123'):
    return User.objects.create_user(username=username, password=password)


def seed_lookup_data():
    genre    = Genre.objects.get_or_create(name='Lo-fi')[0]
    mood     = Mood.objects.get_or_create(name='Calm')[0]
    occasion = Occasion.objects.get_or_create(name='Study')[0]
    singer   = SingerModel.objects.get_or_create(name='Default')[0]
    theme    = Theme.objects.get_or_create(name='Rain')[0]
    return {
        'genre':        genre,
        'mood':         mood,
        'occasion':     occasion,
        'singer_model': singer,
        'theme':        theme,
    }


def valid_form_data(lookup):
    return {
        'title':        'Test Rainy Lo-fi',
        'singer_model': lookup['singer_model'].pk,
        'genre':        lookup['genre'].pk,
        'mood':         lookup['mood'].pk,
        'occasion':     lookup['occasion'].pk,
        'themes':       [lookup['theme'].pk],
        'duration':     30,
        'review_notes': 'Soft piano, no drums',
    }


def make_completed_song(user, lookup, title='Test Song'):
    return Song.objects.create(
        title=title,
        user=user,
        singer_model=lookup['singer_model'],
        genre=lookup['genre'],
        mood=lookup['mood'],
        occasion=lookup['occasion'],
        duration=30,
        review_notes='',
        generation_status=GenerationStatus.COMPLETED,
        audio_url='https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3',
    )


# ============================================================
# AUTH USER STORIES
# ============================================================

@override_settings(
    GENERATOR_STRATEGY='mock',
    SOCIALACCOUNT_PROVIDERS={
        'google': {
            'SCOPE': ['profile', 'email'],
            'AUTH_PARAMS': {'access_type': 'online'},
            'OAUTH_PKCE_ENABLED': True,
        }
    },
)
class US1_GoogleLogin(TestCase):
    """
    US-1: As a user, I want to log in using Google so I don't need
    to create a new account.
    """

    def setUp(self):
        from allauth.socialaccount.models import SocialApp
        from django.contrib.sites.models import Site
        site = Site.objects.get_current()
        SocialApp.objects.filter(provider='google').delete()
        app = SocialApp.objects.create(
            provider='google',
            name='Google',
            client_id='test-client-id',
            secret='test-secret',
        )
        app.sites.add(site)

    def test_google_login_url_exists(self):
        """Google OAuth URL should be reachable (allauth registered)."""
        response = self.client.get('/accounts/google/login/')
        self.assertNotEqual(response.status_code, 404,
            'Google login URL /accounts/google/login/ returned 404 — '
            'allauth may not be installed or configured.')

    def test_login_page_shows_google_option(self):
        """Login page should mention Google sign-in."""
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertTrue(
            'google' in content.lower(),
            'Login page does not mention Google sign-in.'
        )


@override_settings(**MOCK_SETTINGS)
class US2_LoginRequired(TestCase):
    """
    US-2: As the system, I require users to log in before accessing
    features so all content is linked to real accounts.
    """

    def test_library_redirects_unauthenticated(self):
        """Song library must redirect unauthenticated users to login."""
        response = self.client.get(reverse('music:song-library'))
        self.assertIn(response.status_code, [301, 302],
            'Library page should redirect unauthenticated users.')
        self.assertIn('login', response['Location'].lower())

    def test_generate_redirects_unauthenticated(self):
        """Generation form must redirect unauthenticated users."""
        response = self.client.get(reverse('music:song-generate'))
        self.assertIn(response.status_code, [301, 302])
        self.assertIn('login', response['Location'].lower())

    def test_song_detail_redirects_unauthenticated(self):
        """Song detail must redirect unauthenticated users."""
        user   = make_user('u2')
        lookup = seed_lookup_data()
        song   = make_completed_song(user, lookup, 'Private Song')
        response = self.client.get(reverse('music:song-detail', kwargs={'pk': song.pk}))
        self.assertIn(response.status_code, [301, 302])


# ============================================================
# MUSIC GENERATION USER STORIES
# ============================================================

@override_settings(**MOCK_SETTINGS)
class US3_StructuredGenerationForm(TestCase):
    """
    US-3: As a creator, I want to generate music using a structured
    form so the process is simple and guided.
    """

    def setUp(self):
        self.user   = make_user('creator3')
        self.lookup = seed_lookup_data()
        self.client.login(username='creator3', password='testpass123')

    def test_generation_form_loads(self):
        """GET /songs/generate/ should return the form (200)."""
        response = self.client.get(reverse('music:song-generate'))
        self.assertEqual(response.status_code, 200)

    def test_form_has_required_fields(self):
        """Form page must contain all required field labels."""
        response = self.client.get(reverse('music:song-generate'))
        content  = response.content.decode().lower()
        for field in ('title', 'genre', 'mood', 'occasion', 'duration'):
            self.assertIn(field, content,
                f'Generation form is missing field: {field}')


@override_settings(**MOCK_SETTINGS)
class US4_RequiredFieldValidation(TestCase):
    """
    US-4: As the system, I require key fields to ensure consistency.
    Required: title, occasion, genre, singer model, mood.
    """

    def setUp(self):
        self.user   = make_user('creator4')
        self.lookup = seed_lookup_data()
        self.client.login(username='creator4', password='testpass123')

    def test_missing_title_fails(self):
        data = valid_form_data(self.lookup)
        data['title'] = ''
        initial_count = Song.objects.count()
        self.client.post(reverse('music:song-generate'), data, follow=True)
        self.assertEqual(Song.objects.count(), initial_count,
            'Submitting without a title should not create a song.')

    def test_missing_genre_fails(self):
        data = valid_form_data(self.lookup)
        data['genre'] = ''
        initial_count = Song.objects.count()
        self.client.post(reverse('music:song-generate'), data, follow=True)
        self.assertEqual(Song.objects.count(), initial_count,
            'Submitting without a genre should not create a song.')

    def test_title_too_short_fails(self):
        data = valid_form_data(self.lookup)
        data['title'] = 'AB'
        initial_count = Song.objects.count()
        self.client.post(reverse('music:song-generate'), data, follow=True)
        self.assertEqual(Song.objects.count(), initial_count,
            'Title shorter than 3 chars should not create a song.')


@override_settings(**MOCK_SETTINGS)
class US5_OptionalThemes(TestCase):
    """
    US-5: As a creator, I want optional themes so I can customize
    the music context.
    """

    def setUp(self):
        self.user   = make_user('creator5')
        self.lookup = seed_lookup_data()
        self.client.login(username='creator5', password='testpass123')

    def test_generation_without_themes_succeeds(self):
        """Themes are optional — omitting them should still generate."""
        data = valid_form_data(self.lookup)
        data['themes'] = []
        response = self.client.post(reverse('music:song-generate'), data)
        self.assertIn(response.status_code, [200, 302],
            'Generation without themes should not error.')

    def test_generation_with_themes_succeeds(self):
        """Themes can be included."""
        data = valid_form_data(self.lookup)
        response = self.client.post(reverse('music:song-generate'), data)
        self.assertIn(response.status_code, [200, 302])


@override_settings(**MOCK_SETTINGS)
class US6_DurationControl(TestCase):
    """
    US-6: As a creator, I want a duration slider to control song length.
    """

    def setUp(self):
        self.user   = make_user('creator6')
        self.lookup = seed_lookup_data()
        self.client.login(username='creator6', password='testpass123')

    def test_duration_field_present_in_form(self):
        response = self.client.get(reverse('music:song-generate'))
        self.assertIn(b'duration', response.content.lower())

    def test_invalid_duration_rejected(self):
        data = valid_form_data(self.lookup)
        data['duration'] = 9999
        initial_count = Song.objects.count()
        self.client.post(reverse('music:song-generate'), data, follow=True)
        self.assertEqual(Song.objects.count(), initial_count,
            'Duration > 300s should be rejected.')

    def test_valid_duration_accepted(self):
        data = valid_form_data(self.lookup)
        data['duration'] = 60
        response = self.client.post(reverse('music:song-generate'), data)
        self.assertIn(response.status_code, [200, 302])


# ============================================================
# LIBRARY USER STORIES
# ============================================================

@override_settings(**MOCK_SETTINGS)
class US7_PersonalLibrary(TestCase):
    """
    US-7: As a creator, I want my songs saved in a personal library.
    """

    def setUp(self):
        self.user   = make_user('creator7')
        self.lookup = seed_lookup_data()
        self.client.login(username='creator7', password='testpass123')

    def test_library_page_loads(self):
        response = self.client.get(reverse('music:song-library'))
        self.assertEqual(response.status_code, 200)

    def test_song_appears_in_library_after_creation(self):
        make_completed_song(self.user, self.lookup, 'Library Test Song')
        response = self.client.get(reverse('music:song-library'))
        self.assertContains(response, 'Library Test Song')

    def test_other_users_songs_not_visible(self):
        """Songs from other users must NOT appear in this user's library."""
        other = make_user('other7')
        make_completed_song(other, self.lookup, 'Other User Song')
        response = self.client.get(reverse('music:song-library'))
        self.assertNotContains(response, 'Other User Song',
            msg_prefix="Another user's song appeared in current user's library.")


@override_settings(**MOCK_SETTINGS)
class US8_SortSongs(TestCase):
    """
    US-8: As a creator, I want to sort my songs by creation time.
    """

    def setUp(self):
        self.user   = make_user('creator8')
        self.lookup = seed_lookup_data()
        self.client.login(username='creator8', password='testpass123')
        for title in ['Alpha Song', 'Beta Song']:
            make_completed_song(self.user, self.lookup, title)

    def test_sort_newest_loads(self):
        response = self.client.get(reverse('music:song-library') + '?sort=newest')
        self.assertEqual(response.status_code, 200)

    def test_sort_oldest_loads(self):
        response = self.client.get(reverse('music:song-library') + '?sort=oldest')
        self.assertEqual(response.status_code, 200)

    def test_sort_by_title_loads(self):
        response = self.client.get(reverse('music:song-library') + '?sort=title')
        self.assertEqual(response.status_code, 200)

    def test_library_contains_both_songs(self):
        response = self.client.get(reverse('music:song-library'))
        self.assertContains(response, 'Alpha Song')
        self.assertContains(response, 'Beta Song')


@override_settings(**MOCK_SETTINGS)
class US9_DeleteSong(TestCase):
    """
    US-9: As a creator, I want to delete songs I no longer want.
    """

    def setUp(self):
        self.user   = make_user('creator9')
        self.lookup = seed_lookup_data()
        self.client.login(username='creator9', password='testpass123')

    def test_delete_removes_song_from_db(self):
        song = make_completed_song(self.user, self.lookup, 'Delete Me')
        pk   = song.pk
        self.client.post(
            reverse('music:song-detail', kwargs={'pk': pk}),
            {'action': 'delete'},
            follow=True,
        )
        self.assertFalse(Song.objects.filter(pk=pk).exists(),
            'Song was not deleted from the database.')

    def test_cannot_delete_other_users_song(self):
        """Ownership check — other user's song must not be deletable."""
        other = make_user('other9')
        song  = make_completed_song(other, self.lookup, 'Protected Song')
        self.client.post(
            reverse('music:song-detail', kwargs={'pk': song.pk}),
            {'action': 'delete'},
        )
        self.assertTrue(Song.objects.filter(pk=song.pk).exists(),
            "Deleting another user's song should be blocked.")


# ============================================================
# PLAYBACK USER STORIES
# ============================================================

@override_settings(**MOCK_SETTINGS)
class US10_US11_Playback(TestCase):
    """
    US-10: As a user, I want to play songs directly in the browser.
    US-11: As a user, I want full playback control (play, pause, skip).
    """

    def setUp(self):
        self.user   = make_user('creator10')
        self.lookup = seed_lookup_data()
        self.client.login(username='creator10', password='testpass123')
        self.song = make_completed_song(self.user, self.lookup, 'Playback Test')

    def test_song_detail_page_loads(self):
        response = self.client.get(
            reverse('music:song-detail', kwargs={'pk': self.song.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_audio_element_present(self):
        """US-10: <audio> element must be present in the song detail page."""
        response = self.client.get(
            reverse('music:song-detail', kwargs={'pk': self.song.pk})
        )
        self.assertIn(b'<audio', response.content,
            'Song detail page must contain an <audio> element for in-browser playback.')

    def test_audio_has_controls(self):
        """US-11: audio element must have controls attribute (play/pause/skip)."""
        response = self.client.get(
            reverse('music:song-detail', kwargs={'pk': self.song.pk})
        )
        self.assertIn(b'controls', response.content,
            'Audio element must have the controls attribute for play/pause/skip.')

    def test_audio_url_present_in_page(self):
        """Audio URL must be in the page so the browser can load it."""
        response = self.client.get(
            reverse('music:song-detail', kwargs={'pk': self.song.pk})
        )
        self.assertIn(b'soundhelix', response.content,
            'Audio URL not found in song detail page.')


# ============================================================
# SHARING USER STORIES
# ============================================================

@override_settings(**MOCK_SETTINGS)
class US12_ShareSong(TestCase):
    """
    US-12: As a creator, I want to share my songs with others.
    """

    def setUp(self):
        self.user   = make_user('creator12')
        self.lookup = seed_lookup_data()
        self.client.login(username='creator12', password='testpass123')
        self.song = make_completed_song(self.user, self.lookup, 'Share Me')
        self.song.is_shared = False
        self.song.save()

    def test_sharing_sets_is_shared_true(self):
        self.client.post(
            reverse('music:song-detail', kwargs={'pk': self.song.pk}),
            {'action': 'share'},
        )
        self.song.refresh_from_db()
        self.assertTrue(self.song.is_shared,
            'Sharing a song should set is_shared=True in the database.')

    def test_unsharing_sets_is_shared_false(self):
        self.song.is_shared = True
        self.song.save()
        self.client.post(
            reverse('music:song-detail', kwargs={'pk': self.song.pk}),
            {'action': 'unshare'},
        )
        self.song.refresh_from_db()
        self.assertFalse(self.song.is_shared,
            'Unsharing a song should set is_shared=False.')


@override_settings(**MOCK_SETTINGS)
class US13_SharedSongListenOnly(TestCase):
    """
    US-13: As a listener, I want to explore shared songs without
    adding them to my library.
    """

    def setUp(self):
        self.owner  = make_user('owner13')
        self.lookup = seed_lookup_data()
        self.song   = make_completed_song(self.owner, self.lookup, 'Publicly Shared Song')
        self.song.is_shared = True
        self.song.save()

    def test_shared_song_accessible_without_login(self):
        """Public shared URL must be accessible to unauthenticated users."""
        anon_client = Client()
        response    = anon_client.get(
            reverse('music:shared-song', kwargs={'song_id': self.song.pk})
        )
        self.assertEqual(response.status_code, 200,
            'Shared song page should be accessible without login.')

    def test_shared_page_has_audio_player(self):
        """Shared page must contain an audio player."""
        anon_client = Client()
        response    = anon_client.get(
            reverse('music:shared-song', kwargs={'song_id': self.song.pk})
        )
        self.assertIn(b'<audio', response.content,
            'Shared song page must contain an audio player.')

    def test_unshared_song_not_accessible(self):
        """Non-shared songs must return 404 on the public URL."""
        self.song.is_shared = False
        self.song.save()
        anon_client = Client()
        response    = anon_client.get(
            reverse('music:shared-song', kwargs={'song_id': self.song.pk})
        )
        self.assertEqual(response.status_code, 404,
            'Unshared songs must not be accessible via public URL.')


@override_settings(**MOCK_SETTINGS)
class US14_FeedbackAfterGeneration(TestCase):
    """
    US-14: As a creator, I want to give feedback so the system
    improves over time.
    """

    def setUp(self):
        self.user   = make_user('creator14')
        self.lookup = seed_lookup_data()
        self.client.login(username='creator14', password='testpass123')

    def test_feedback_url_accessible(self):
        """Feedback page must be accessible to logged-in users."""
        response = self.client.get(reverse('music:feedback'))
        self.assertEqual(response.status_code, 200,
            'Feedback page must be accessible at /songs/feedback/')

    def test_feedback_form_present(self):
        """Feedback page must contain a form."""
        response = self.client.get(reverse('music:feedback'))
        self.assertIn(b'<form', response.content,
            'Feedback page must contain a form element.')

    def test_feedback_link_visible_on_completed_song(self):
        """Song detail page must show a feedback link when song is completed."""
        song = make_completed_song(
            self.user, self.lookup, 'Completed Song For Feedback'
        )
        response = self.client.get(
            reverse('music:song-detail', kwargs={'pk': song.pk})
        )
        content = response.content.decode().lower()
        self.assertTrue(
            'feedback' in content,
            'Song detail page for a COMPLETED song must contain a feedback link.'
        )


# ============================================================
# MOCK STRATEGY SPECIFIC TESTS
# ============================================================

@override_settings(**MOCK_SETTINGS)
class MockStrategyIntegration(TestCase):
    """
    Verify that the Mock strategy correctly integrates with the service layer
    and produces an immediate SUCCESS result (no external API calls).
    """

    def setUp(self):
        self.lookup = seed_lookup_data()

    def test_mock_strategy_generates_immediately(self):
        """Mock strategy must return status=SUCCESS with a non-empty audio_url."""
        from music.strategies.mock_strategy import MockSongGeneratorStrategy
        strategy = MockSongGeneratorStrategy()
        result   = strategy.generate({
            'title': 'Test', 'prompt': 'test prompt',
            'genre': 'Lo-fi', 'mood': 'Calm', 'duration': 30,
        })
        self.assertEqual(result['status'], 'SUCCESS')
        self.assertTrue(result['audio_url'],
            'Mock strategy must return a non-empty audio_url.')
        self.assertEqual(result['task_id'], '',
            'Mock strategy must return an empty task_id.')

    def test_factory_returns_mock_when_configured(self):
        """StrategyFactory must return MockSongGeneratorStrategy when setting=mock."""
        from music.strategies.factory import StrategyFactory
        from music.strategies.mock_strategy import MockSongGeneratorStrategy
        strategy = StrategyFactory.get_strategy()
        self.assertIsInstance(strategy, MockSongGeneratorStrategy,
            'Factory must return MockSongGeneratorStrategy when GENERATOR_STRATEGY=mock.')

    def test_service_creates_completed_song_with_mock(self):
        """
        Full service-layer integration: generate_song() with mock must
        create a COMPLETED Song with an audio_url.
        """
        from music.services import SongGenerationService
        user    = make_user('svc_test')
        service = SongGenerationService()
        data    = {
            'title':        'Service Integration Test',
            'singer_model': self.lookup['singer_model'],
            'genre':        self.lookup['genre'],
            'mood':         self.lookup['mood'],
            'occasion':     self.lookup['occasion'],
            'themes':       [],
            'duration':     30,
            'review_notes': '',
        }
        song = service.generate_song(user=user, form_data=data)
        self.assertEqual(song.generation_status, GenerationStatus.COMPLETED,
            'Service must mark song as COMPLETED after mock generation.')
        self.assertTrue(song.audio_url,
            'Service must save the mock audio_url to the Song record.')
        self.assertEqual(song.user, user,
            'Song must be linked to the correct user.')
