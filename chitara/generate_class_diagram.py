"""
Chitara Class Diagram — Dark Theme
Run: python generate_class_diagram.py
Output: diagrams/class_diagram.png
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ── CONFIG ───────────────────────────────────────────────────────────────────
BG       = '#0d0d0d'
FIG_W, FIG_H = 32, 22

COLORS = {
    'presentation': ('#1e3a5f', '#3b82f6'),
    'service':      ('#3b1a08', '#f97316'),
    'strategy_abc': ('#2d0a4e', '#a855f7'),
    'strategy':     ('#3a0a50', '#c084fc'),
    'factory':      ('#12104a', '#818cf8'),
    'persistence':  ('#3a0a0a', '#ef4444'),
    'repository':   ('#1a0a2e', '#a78bfa'),
    'model':        ('#0a1a2e', '#60a5fa'),
    'exception':    ('#2a0a0a', '#f87171'),
    'external':     ('#1a1a1a', '#6b7280'),
}

def draw_box(ax, x, y, w, title, stereotype, attrs,
             color_key, title_fs=7.5, attr_fs=6.2,
             line_h=0.22, pad=0.18):
    bg_color, border_color = COLORS[color_key]

    n_attrs  = len(attrs)
    hdr_h    = 0.55 if stereotype else 0.42
    body_h   = max(0.3, n_attrs * line_h + pad * 2)
    total_h  = hdr_h + body_h

    ax.add_patch(plt.Rectangle(
        (x, y + body_h), w, hdr_h,
        facecolor=border_color, edgecolor=border_color, lw=0, zorder=2
    ))
    ax.add_patch(plt.Rectangle(
        (x, y), w, body_h,
        facecolor=bg_color, edgecolor=border_color, lw=1.4, zorder=2
    ))
    ax.add_patch(plt.Rectangle(
        (x, y), w, total_h,
        facecolor='none', edgecolor=border_color, lw=1.4, zorder=3
    ))

    ty = y + body_h + hdr_h
    if stereotype:
        ax.text(x + w/2, ty - 0.16, f'«{stereotype}»',
                ha='center', va='top', fontsize=5.5,
                color='white', alpha=0.85, zorder=4)
        ax.text(x + w/2, ty - 0.36, title,
                ha='center', va='top', fontsize=title_fs,
                fontweight='bold', color='white', zorder=4)
    else:
        ax.text(x + w/2, ty - 0.22, title,
                ha='center', va='top', fontsize=title_fs,
                fontweight='bold', color='white', zorder=4)

    for i, attr in enumerate(attrs):
        ay = y + body_h - pad - i * line_h
        max_chars = int(w / 0.072)
        display   = attr if len(attr) <= max_chars else attr[:max_chars-2] + '…'
        ax.text(x + 0.1, ay, display,
                ha='left', va='top',
                fontsize=attr_fs, color='#c8c8d8',
                fontfamily='monospace', zorder=4)

    return total_h


def arrow(ax, x1, y1, x2, y2, label='', style='->', color='#6b7280'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle=style, color=color, lw=1.0),
        zorder=1)
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx, my + 0.12, label, ha='center', fontsize=5.5,
                color='#9ca3af', style='italic', zorder=4)


def layer_band(ax, y, h, label, color, fig_w=FIG_W):
    ax.add_patch(plt.Rectangle(
        (0.2, y), fig_w - 0.4, h,
        facecolor=color, edgecolor='none', alpha=0.08, zorder=0
    ))
    ax.text(0.4, y + h - 0.15, label,
            ha='left', va='top', fontsize=7,
            color='#9ca3af', fontweight='bold', zorder=1)


fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.set_facecolor(BG)
fig.patch.set_facecolor(BG)
ax.axis('off')

# ── LAYER BANDS ───────────────────────────────────────────────────────────────
layer_band(ax, 19.0, 2.6,  'PRESENTATION LAYER',           '#1e3a5f')
layer_band(ax, 14.5, 4.2,  'CONTROLLER LAYER',             '#14532d')
layer_band(ax, 10.0, 4.2,  'BUSINESS LOGIC (Services)',    '#7c2d12')
layer_band(ax,  5.5, 4.2,  'PERSISTENCE (Repos + Models)', '#7f1d1d')
layer_band(ax,  0.5, 4.7,  'STRATEGY PATTERN',             '#3b0764')

# ── PRESENTATION ─────────────────────────────────────────────────────────────
BOX_W = 3.8
views = [
    ('SongGenerationView',        'View', ['+ form_class', '+ get()', '+ post()', '+ form_valid()']),
    ('SongGenerationPreviewView', 'View', ['+ get()', '+ post()', '- _get_form_from_session()']),
    ('SongLibraryView',           'View', ['+ paginate_by = 20', '+ get_queryset()', '+ get_context_data()']),
    ('SongDetailView',            'View', ['+ get_object()', '+ get_context_data()', '+ post()']),
    ('FeedbackView',              'View', ['+ fields: list', '+ form_valid()', '+ get_success_url()']),
    ('SharedSongView',            'View', ['+ pk_url_kwarg', '+ get_object()', '+ get_context_data()']),
    ('SunoCallbackView',          'View', ['+ post(request)']),
]
for i, (name, stereo, attrs) in enumerate(views):
    x = 0.4 + i * (BOX_W + 0.35)
    draw_box(ax, x, 19.2, BOX_W, name, stereo, attrs, 'presentation')

# ── SERVICES ─────────────────────────────────────────────────────────────────
draw_box(ax, 0.5, 10.3, 5.5, 'SongGenerationService', 'Service', [
    '+ repository: SongRepository',
    '+ generate_song(user, form_data)',
    '+ get_user_songs(user)',
    '- _validate_request(form_data)',
    '- _build_prompt(song)',
], 'service')

draw_box(ax, 7.0, 10.3, 5.5, 'SongLibraryService', 'Service', [
    '+ repository: SongRepository',
    '+ get_library(user)',
    '+ search_songs(user, query)',
    '+ get_statistics(user)',
    '+ delete_song(song_id, user)',
    '+ share_song(song_id, user)',
    '+ unshare_song(song_id, user)',
], 'service')

draw_box(ax, 14.0, 10.8, 4.5, 'InvalidGenerationInput', 'Exception', [
    '(extends Exception)',
], 'exception')

draw_box(ax, 19.5, 10.8, 4.5, 'SongGenerationError', 'Exception', [
    '(extends Exception)',
], 'exception')

# ── REPOSITORY ────────────────────────────────────────────────────────────────
draw_box(ax, 0.5, 5.8, 5.0, 'SongRepository', 'Repository', [
    '+ save(song)',
    '+ get_song(song_id, user)',
    '+ get_user_songs(user)',
    '+ update_generation_status()',
    '+ update_audio_url(song, url)',
    '+ delete(song)',
], 'repository')

draw_box(ax, 6.5, 6.2, 3.5, 'RepositoryError', 'Exception', [
    '(extends Exception)',
], 'exception')

# ── MODELS ───────────────────────────────────────────────────────────────────
draw_box(ax, 11.0, 5.5, 4.2, 'Song', 'Model', [
    '+ title: CharField(100)',
    '+ duration: PositiveIntegerField',
    '+ generation_status: TextChoices',
    '+ audio_url: URLField',
    '+ image_url: URLField',
    '+ is_shared: BooleanField',
    '+ external_id: CharField',
    '+ review_notes: TextField',
    '+ created_at: DateTimeField',
    '+ user: FK(User)',
    '+ genre: FK(Genre)',
    '+ mood: FK(Mood)',
    '+ occasion: FK(Occasion)',
    '+ singer_model: FK(SingerModel)',
    '+ themes: M2M(Theme)',
], 'model')

lookup_models = [
    (16.5, 6.5, 'Genre',       ['+ name: CharField']),
    (20.0, 6.5, 'Mood',        ['+ name: CharField']),
    (23.5, 6.5, 'Occasion',    ['+ name: CharField']),
    (16.5, 5.2, 'Theme',       ['+ name: CharField']),
    (20.0, 5.2, 'SingerModel', ['+ name: CharField', '+ description: TextField']),
    (23.5, 5.2, 'GenerationStatus', ['PENDING', 'GENERATING', 'COMPLETED', 'FAILED']),
]
for lx, ly, lname, lattrs in lookup_models:
    stereo = 'TextChoices' if lname == 'GenerationStatus' else 'Model'
    draw_box(ax, lx, ly, 3.0, lname, stereo, lattrs, 'model')

# ── STRATEGY PATTERN ──────────────────────────────────────────────────────────
draw_box(ax, 0.5, 1.0, 5.5, 'SongGeneratorStrategy', 'ABC', [
    '@abstractmethod',
    '+ generate(song_request) -> dict',
], 'strategy_abc')

draw_box(ax, 7.5, 1.0, 5.5, 'MockSongGeneratorStrategy', 'Strategy', [
    '+ generate(song_request) -> dict',
    '  Returns fixed audio URL',
    '  No external API calls',
    '  status: SUCCESS (instant)',
], 'strategy')

draw_box(ax, 14.5, 1.0, 6.0, 'SunoSongGeneratorStrategy', 'Strategy', [
    '+ generate(song_request, song)',
    '- _build_payload(song_request)',
    '- _create_task(payload)',
    '- _poll_status(task_id)',
    '- _poll_until_done(task_id, song)',
    '- _update_song(song, clip, ok)',
], 'strategy')

draw_box(ax, 22.0, 1.0, 5.5, 'StrategyFactory', 'Factory', [
    '+ get_strategy(force_mock=False)',
    '  Reads GENERATOR_STRATEGY env',
    '  Falls back to mock if no key',
], 'factory')

# ── TITLE ─────────────────────────────────────────────────────────────────────
ax.text(FIG_W/2, FIG_H - 0.3, 'Chitara — Class Diagram',
        ha='center', fontsize=16, fontweight='bold', color='white')
ax.text(FIG_W/2, FIG_H - 0.75, 'MVT + Service + Repository + Strategy Pattern',
        ha='center', fontsize=9, color='#9ca3af')

# ── LEGEND ────────────────────────────────────────────────────────────────────
legend_items = [
    mpatches.Patch(color='#3b82f6', label='Presentation (Views)'),
    mpatches.Patch(color='#22c55e', label='Controller (Views)'),
    mpatches.Patch(color='#f97316', label='Business Logic (Services)'),
    mpatches.Patch(color='#ef4444', label='Persistence (Repos/Models)'),
    mpatches.Patch(color='#a855f7', label='Strategy Pattern'),
]
ax.legend(handles=legend_items, loc='lower right',
          fontsize=7, framealpha=0.2,
          facecolor='#1a1a1a', edgecolor='#444',
          labelcolor='white',
          bbox_to_anchor=(0.99, 0.01))

# ── ARROWS ────────────────────────────────────────────────────────────────────
arrow(ax, 3.2, 10.3, 3.2, 8.0, 'uses')
arrow(ax, 6.0, 12.0, 10.5, 3.5, 'uses')
arrow(ax, 22.0, 2.5, 13.5, 2.5, 'creates')
arrow(ax, 22.0, 2.2, 20.5, 2.2, 'creates')
arrow(ax, 7.5, 2.5, 6.0, 2.5, '-|>', color='#a855f7')
arrow(ax, 14.5, 2.5, 6.0, 2.2, '-|>', color='#a855f7')
arrow(ax, 5.5, 7.5, 11.0, 7.5, 'CRUD')

os.makedirs('diagrams', exist_ok=True)
plt.tight_layout(pad=0.2)
plt.savefig('diagrams/class_diagram.png', dpi=150,
            bbox_inches='tight', facecolor=BG)
plt.close()
print('Saved: diagrams/class_diagram.png')
