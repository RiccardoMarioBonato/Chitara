"""
Presentation Layer — forms.py
Handles user input validation for the Chitara music generation app.
No business logic lives here; only input shape and basic field-level rules.
"""

from django import forms

from .models import Genre, Mood, Occasion, SingerModel, Song, Theme

DURATION_MIN = 30
DURATION_MAX = 300


class SongGenerationForm(forms.ModelForm):
    """
    ModelForm for requesting a new AI-generated song.

    Excluded fields (set programmatically by the view/service):
        user, generation_status, is_shared, created_at, audio_url
    """

    title = forms.CharField(
        min_length=3,
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Sunset Memories',
        }),
        help_text='Between 3 and 255 characters.',
        error_messages={
            'required': 'Please give your song a title.',
            'min_length': 'Title must be at least 3 characters long.',
            'max_length': 'Title cannot exceed 255 characters.',
        },
    )

    singer_model = forms.ModelChoiceField(
        queryset=SingerModel.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='— Select a voice model —',
        error_messages={'required': 'Please select a voice model.'},
    )

    genre = forms.ModelChoiceField(
        queryset=Genre.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='— Select a genre —',
        error_messages={'required': 'Please select a genre.'},
    )

    mood = forms.ModelChoiceField(
        queryset=Mood.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='— Select a mood —',
        error_messages={'required': 'Please select a mood.'},
    )

    # occasion is NOT NULL in the DB — kept required here to match the model.
    # If the diagram marks it optional, add a nullable migration first.
    occasion = forms.ModelChoiceField(
        queryset=Occasion.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='— Select an occasion —',
        error_messages={'required': 'Please select an occasion.'},
    )

    themes = forms.ModelMultipleChoiceField(
        queryset=Theme.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        help_text='Optional — choose one or more themes.',
    )

    review_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any extra notes or lyrics hints for the AI…',
        }),
        help_text='Optional creative notes passed to the AI.',
    )

    duration = forms.IntegerField(
        min_value=DURATION_MIN,
        max_value=DURATION_MAX,
        initial=120,
        required=True,
        error_messages={
            'required':  'Duration is required.',
            'invalid':   'Duration must be a whole number.',
            'min_value': 'Minimum duration is 30 seconds.',
            'max_value': 'Maximum duration is 300 seconds.',
        },
    )

    class Meta:
        model = Song
        fields = [
            'title',
            'singer_model',
            'genre',
            'mood',
            'occasion',
            'themes',
            'review_notes',
            'duration',
        ]

    # ------------------------------------------------------------------
    # Field-level validators
    # ------------------------------------------------------------------

    def clean_title(self) -> str:
        """
        Ensure the title contains at least one alphabetic character and
        does not consist of whitespace or punctuation only.
        """
        title: str = self.cleaned_data.get('title', '').strip()

        if not any(c.isalpha() for c in title):
            raise forms.ValidationError(
                'Title must contain at least one letter.'
            )

        return title

    def clean_duration(self) -> int:
        duration: int = self.cleaned_data.get('duration')
        if duration is not None and not (DURATION_MIN <= duration <= DURATION_MAX):
            raise forms.ValidationError(
                f'Duration must be between {DURATION_MIN} and {DURATION_MAX} seconds.'
            )
        return duration

    # ------------------------------------------------------------------
    # Cross-field validation
    # ------------------------------------------------------------------

    def clean(self) -> dict:
        """Cross-field validation rules."""
        cleaned = super().clean()

        genre = cleaned.get('genre')
        mood  = cleaned.get('mood')

        # Example cross-field rule: flag obviously mismatched combinations
        # so the user gets early feedback rather than a bad generation.
        if genre and mood:
            incompatible_pairs = {
                ('Heavy Metal', 'Calm'),
                ('Lullaby',     'Angry'),
            }
            pair = (str(genre), str(mood))
            if pair in incompatible_pairs:
                raise forms.ValidationError(
                    f'"{genre}" and "{mood}" are unlikely to produce good '
                    'results together. Please adjust your selection.'
                )

        return cleaned
