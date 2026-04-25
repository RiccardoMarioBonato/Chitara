"""
Generates the Chitara class diagram (MVT + Strategy + Repository layers).
Run: python generate_class_diagram.py
Output: diagrams/class_diagram.png
"""

import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(figsize=(26, 18))
ax.set_xlim(0, 26)
ax.set_ylim(0, 18)
ax.axis('off')
fig.patch.set_facecolor('#f8f9fa')


def box(ax, x, y, w, h, title, stereotype, members, hdr_color, lw=1.4):
    """Draw a UML class box with header + body."""
    ax.add_patch(FancyBboxPatch((x, y + h * 0.45), w, h * 0.55,
        boxstyle='round,pad=0.04', facecolor=hdr_color, edgecolor='#333', lw=lw))
    if stereotype:
        ax.text(x + w / 2, y + h * 0.88, f'«{stereotype}»',
                ha='center', va='center', fontsize=6, color='#eee')
    ax.text(x + w / 2, y + h * 0.67, title, ha='center', va='center',
            fontsize=8, fontweight='bold', color='white')
    ax.add_patch(FancyBboxPatch((x, y), w, h * 0.45,
        boxstyle='round,pad=0.04', facecolor='white', edgecolor='#333', lw=lw))
    step = h * 0.42 / max(len(members), 1)
    for i, m in enumerate(members):
        ax.text(x + 0.08, y + h * 0.42 - i * step, m,
                ha='left', va='top', fontsize=5.8, fontfamily='monospace')


def arr(ax, x1, y1, x2, y2, style='->', color='#333', curve=0.0, lw=1.1):
    cs = f'arc3,rad={curve}' if curve else 'arc3,rad=0'
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle=style, color=color, lw=lw,
                        connectionstyle=cs))


def layer_band(ax, y, h, label, color):
    ax.add_patch(plt.Rectangle((0.1, y), 25.8, h,
        facecolor=color, edgecolor='#ccc', lw=0.6, alpha=0.25, zorder=0))
    ax.text(0.25, y + h / 2, label, ha='left', va='center',
            fontsize=8, fontweight='bold', color='#555', alpha=0.7)


# ── Layer bands ───────────────────────────────────────────────────────────────
layer_band(ax, 14.5, 3.3,  'PRESENTATION LAYER  (Views / Templates)',   '#bbdefb')
layer_band(ax, 10.0, 4.2,  'BUSINESS LOGIC LAYER  (Services)',           '#c8e6c9')
layer_band(ax, 5.5,  4.2,  'PERSISTENCE LAYER  (Repositories / Models)', '#fff9c4')
layer_band(ax, 0.2,  5.0,  'STRATEGY LAYER  (Pattern)',                  '#e1bee7')

# ── PRESENTATION LAYER ────────────────────────────────────────────────────────

box(ax, 1.0, 14.8, 3.2, 2.4, 'SongGenerationView', 'View',
    ['+form_class: SongGenerationForm', '+get_context_data()', '+form_valid()',
     '+form_invalid()'],
    '#1565c0')

box(ax, 4.5, 14.8, 3.2, 2.4, 'SongGenerationPreviewView', 'View',
    ['+get(request)', '+post(request)',
     '-_get_form_from_session()'],
    '#1565c0')

box(ax, 8.1, 14.8, 3.0, 2.4, 'SongLibraryView', 'View',
    ['+paginate_by: int = 20', '+get_queryset()',
     '+get_context_data()'],
    '#1565c0')

box(ax, 11.4, 14.8, 3.0, 2.4, 'SongDetailView', 'View',
    ['+get_object()', '+get_context_data()',
     '+post(request)'],
    '#1565c0')

box(ax, 14.7, 14.8, 2.8, 2.4, 'FeedbackView', 'View',
    ['+fields: list', '+form_valid(form)'],
    '#1565c0')

box(ax, 17.8, 14.8, 3.0, 2.4, 'SharedSongView', 'View',
    ['+pk_url_kwarg: str',
     '+get_object()',
     '+get_context_data()'],
    '#1565c0')

box(ax, 21.1, 14.8, 2.8, 2.4, 'SunoCallbackView', 'View',
    ['+post(request)'],
    '#1565c0')

# ── BUSINESS LOGIC LAYER ──────────────────────────────────────────────────────

box(ax, 2.0, 10.5, 4.5, 3.2, 'SongGenerationService', 'Service',
    ['+repository: SongRepository',
     '+generate_song(user, form_data)',
     '+get_user_songs(user)',
     '-_validate_request(form_data)',
     '-_build_prompt(song)'],
    '#2e7d32')

box(ax, 7.5, 10.5, 4.0, 3.2, 'SongLibraryService', 'Service',
    ['+repository: SongRepository',
     '+get_library(user)',
     '+search_songs(user, query)',
     '+get_statistics(user)',
     '+delete_song(id, user)',
     '+share_song(id, user)'],
    '#2e7d32')

box(ax, 12.5, 10.5, 3.5, 2.0, 'InvalidGenerationInput', 'Exception',
    ['(extends Exception)'],
    '#c62828')

box(ax, 16.5, 10.5, 3.0, 2.0, 'SongGenerationError', 'Exception',
    ['(extends Exception)'],
    '#c62828')

# ── PERSISTENCE LAYER ─────────────────────────────────────────────────────────

box(ax, 1.5, 6.2, 4.5, 3.0, 'SongRepository', 'Repository',
    ['+save(song)',
     '+get_song(id, user)',
     '+get_user_songs(user)',
     '+update_generation_status(song, status)',
     '+update_audio_url(song, url)',
     '+delete(song)'],
    '#f57f17')

box(ax, 7.0, 6.2, 3.0, 1.8, 'RepositoryError', 'Exception',
    ['(extends Exception)'],
    '#e65100')

box(ax, 11.0, 6.2, 3.0, 3.0, 'Song', 'Model',
    ['+title, duration, review_notes',
     '+generation_status: TextChoices',
     '+audio_url, image_url: URLField',
     '+is_shared: BooleanField',
     '+user: FK(User)',
     '+genre, mood, occasion: FK'],
    '#827717')

box(ax, 15.0, 6.2, 2.5, 2.0, 'Genre', 'Model',   ['+name: CharField'], '#827717')
box(ax, 17.8, 6.2, 2.5, 2.0, 'Mood',  'Model',   ['+name: CharField'], '#827717')
box(ax, 20.6, 6.2, 2.5, 2.0, 'Occasion','Model', ['+name: CharField'], '#827717')
box(ax, 23.4, 6.2, 2.5, 2.0, 'Theme',  'Model',  ['+name: CharField'], '#827717')

# ── STRATEGY LAYER ────────────────────────────────────────────────────────────

box(ax, 1.0, 1.5, 4.5, 3.0, 'SongGeneratorStrategy', 'ABC',
    ['«abstract»',
     '+generate(song_request) → dict'],
    '#6a1b9a')

box(ax, 7.0, 1.5, 4.5, 3.0, 'MockSongGeneratorStrategy', 'Strategy',
    ['+generate(song_request) → dict',
     '# Returns fixed audio URL',
     '# No external API call'],
    '#7b1fa2')

box(ax, 13.0, 1.5, 5.0, 3.0, 'SunoSongGeneratorStrategy', 'Strategy',
    ['+generate(song_request) → dict',
     '-_create_task(payload)',
     '-_poll_status(task_id)',
     '-_poll_until_done(task_id, song)'],
    '#7b1fa2')

box(ax, 19.5, 1.5, 4.5, 3.0, 'StrategyFactory', 'Factory',
    ['+get_strategy(force_mock=False)',
     '# Reads GENERATOR_STRATEGY env',
     '# Falls back to mock if no key'],
    '#4a148c')

# ── Relationships ─────────────────────────────────────────────────────────────

# Views → Services
arr(ax, 4.0, 14.8, 4.2, 13.7, '->', '#555', 0.1)
arr(ax, 10.0, 14.8, 9.5, 13.7, '->', '#555', 0.0)
arr(ax, 13.0, 14.8, 9.5, 13.7, '->', '#555', 0.1)

# Services → Repository
arr(ax, 4.2, 10.5, 3.7, 9.2, '->', '#555', 0.0)
arr(ax, 9.0, 10.5, 5.0, 9.2, '->', '#555', 0.15)

# Services → Strategy Factory
arr(ax, 4.5, 10.5, 20.5, 4.5, '->', '#777', -0.25)

# Repository → Song Model
arr(ax, 5.5, 6.2, 11.0, 7.5, '->', '#777', 0.0)

# Strategy Inheritance
arr(ax, 9.2, 3.0, 5.5, 3.0, '->', '#6a1b9a', 0.0)
arr(ax, 15.5, 3.0, 5.5, 2.8, '->', '#6a1b9a', 0.1)

# Factory → Strategies
arr(ax, 20.5, 3.5, 18.0, 3.2, '->', '#4a148c', 0.1)
arr(ax, 20.5, 3.5, 11.5, 3.2, '->', '#4a148c', 0.1)

# ── Title & Legend ────────────────────────────────────────────────────────────

ax.text(13, 17.6, 'Chitara — Class Diagram', ha='center',
        fontsize=15, fontweight='bold', color='#1a237e')
ax.text(13, 17.25, 'MVT + Strategy + Repository architecture', ha='center',
        fontsize=9.5, color='#555')

patches = [
    mpatches.Patch(color='#bbdefb', alpha=0.6, label='Presentation  (Views)'),
    mpatches.Patch(color='#c8e6c9', alpha=0.6, label='Business Logic  (Services)'),
    mpatches.Patch(color='#fff9c4', alpha=0.6, label='Persistence  (Repos / Models)'),
    mpatches.Patch(color='#e1bee7', alpha=0.6, label='Strategy  (Pattern)'),
]
ax.legend(handles=patches, loc='lower right', fontsize=8, framealpha=0.9)

os.makedirs('diagrams', exist_ok=True)
plt.tight_layout()
plt.savefig('diagrams/class_diagram.png', dpi=150, bbox_inches='tight', facecolor='#f8f9fa')
plt.close()
print('Saved: diagrams/class_diagram.png')
