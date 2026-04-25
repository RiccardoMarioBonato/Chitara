"""
Generates the Chitara song generation sequence diagram.
Run: python generate_sequence_diagram.py
Output: diagrams/sequence_diagram.png
"""

import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(24, 17))
ax.set_xlim(0, 24)
ax.set_ylim(0, 17)
ax.axis('off')
fig.patch.set_facecolor('#fafafa')

# ── Lifelines ─────────────────────────────────────────────────────────────────

ACTORS = [
    (1.2,  'User\n(Browser)'),
    (3.8,  'Song\nGenerationView'),
    (6.8,  'Song\nPreviewView'),
    (9.8,  'Song\nGeneration\nService'),
    (12.8, 'Strategy\nFactory'),
    (15.8, 'Mock /\nSuno Strategy'),
    (19.0, 'Song\nRepository'),
    (22.5, 'Suno API\n(External)'),
]

HDR_COLORS = [
    '#1565c0', '#2e7d32', '#2e7d32', '#e65100',
    '#4a148c', '#7b1fa2', '#880e4f', '#37474f',
]

for (x, name), color in zip(ACTORS, HDR_COLORS):
    ax.add_patch(plt.Rectangle((x - 0.9, 14.5), 1.8, 1.1,
        facecolor=color, edgecolor='#222', lw=1.2))
    ax.text(x, 15.05, name, ha='center', va='center',
            fontsize=6, fontweight='bold', color='white')
    ax.plot([x, x], [14.5, 0.3], color='#bbb', lw=0.9, linestyle='--', zorder=0)


def msg(ax, x1, x2, y, label, ret=False, note=''):
    style = '<-' if ret else '->'
    color = '#555' if ret else '#111'
    ax.annotate('', xy=(x2, y), xytext=(x1, y),
        arrowprops=dict(arrowstyle=style, color=color, lw=1.1))
    mid = (x1 + x2) / 2
    ax.text(mid, y + 0.12, label, ha='center', va='bottom', fontsize=6.2, color='#111')
    if note:
        ax.text(max(x1, x2) + 0.1, y, note, ha='left', va='center', fontsize=5.5, color='#666')


def divider(ax, y, label, color='#e3f2fd'):
    ax.add_patch(plt.Rectangle((0.2, y - 0.17), 23.6, 0.34,
        facecolor=color, edgecolor='#bbb', lw=0.7, alpha=0.7))
    ax.text(0.4, y, label, ha='left', va='center', fontsize=7, fontweight='bold', color='#333')


def act(ax, x, y_top, y_bot, color='#e8f5e9'):
    ax.add_patch(plt.Rectangle((x - 0.14, y_bot), 0.28, y_top - y_bot,
        facecolor=color, edgecolor='#555', lw=0.7, zorder=2))


# ── Title ─────────────────────────────────────────────────────────────────────

ax.text(12, 16.6, 'Chitara — Song Generation Sequence Diagram',
        ha='center', fontsize=13, fontweight='bold', color='#1a237e')
ax.text(12, 16.25,
        'Form → Preview → Confirm → Strategy Dispatch (Mock / Suno) → DB Persist',
        ha='center', fontsize=8, color='#555')

# ── PHASE 1: Form ─────────────────────────────────────────────────────────────

divider(ax, 14.1, 'PHASE 1 — Generation Form', '#e3f2fd')
act(ax, 3.8, 14.0, 12.0)

msg(ax, 1.2, 3.8, 13.8, 'GET /songs/generate/')
msg(ax, 3.8, 1.2, 13.5, '200  SongGenerationForm (genre, mood, occasion…)', ret=True)
msg(ax, 1.2, 3.8, 13.2, 'POST /songs/generate/ {title, genre, mood, duration, …}')
msg(ax, 3.8, 6.8, 12.9, 'session["song_preview_data"] = form_data')
msg(ax, 3.8, 1.2, 12.6, '302  redirect → /songs/generate/preview/', ret=True)

# ── PHASE 2: Preview ──────────────────────────────────────────────────────────

divider(ax, 12.3, 'PHASE 2 — Preview & Confirm', '#e8f5e9')
act(ax, 6.8, 12.2, 10.2)

msg(ax, 1.2, 6.8, 12.1, 'GET /songs/generate/preview/')
msg(ax, 6.8, 1.2, 11.8, '200  song_preview.html {summary of choices}', ret=True)
msg(ax, 1.2, 6.8, 11.5, 'POST /songs/generate/preview/  (Confirm & Generate)')

# ── PHASE 3: Generation Dispatch ─────────────────────────────────────────────

divider(ax, 11.2, 'PHASE 3 — Strategy Dispatch', '#fff3e0')
act(ax, 6.8,  11.1, 9.8)
act(ax, 9.8,  11.1, 7.5)
act(ax, 12.8, 11.0, 9.0)
act(ax, 19.0, 10.8, 9.4)

msg(ax, 6.8,  9.8, 11.0, 'service.generate_song(user, form_data)')
msg(ax, 9.8,  19.0, 10.7, 'repository.save(song)  [status=PENDING]')
msg(ax, 19.0, 9.8, 10.4, 'song  (pk assigned)', ret=True)
msg(ax, 9.8,  12.8, 10.1, 'StrategyFactory.get_strategy()')

# Suno branch label
ax.text(13.3, 9.75, '[ GENERATOR_STRATEGY = mock ]',
        fontsize=6.5, color='#7b1fa2', style='italic',
        bbox=dict(boxstyle='round', facecolor='#ede7f6', alpha=0.6))
msg(ax, 12.8, 9.8, 9.7, 'MockSongGeneratorStrategy()', ret=True, note='← factory decision')

# ── Mock path ─────────────────────────────────────────────────────────────────

act(ax, 15.8, 9.5, 8.3)
msg(ax, 9.8,  15.8, 9.4, 'strategy.generate(song_request)')
msg(ax, 15.8, 9.8, 8.6, '{status: SUCCESS, audio_url: soundhelix.mp3, task_id: ""}', ret=True)

# ── Suno path ─────────────────────────────────────────────────────────────────

ax.text(13.3, 8.35, '[ GENERATOR_STRATEGY = suno ]',
        fontsize=6.5, color='#37474f', style='italic',
        bbox=dict(boxstyle='round', facecolor='#eceff1', alpha=0.6))
act(ax, 15.8, 8.25, 6.4)
act(ax, 22.5, 8.1, 7.3)

msg(ax, 9.8, 15.8, 8.2, 'strategy.generate(song_request, song_instance=song)')
msg(ax, 15.8, 22.5, 7.9, 'POST /api/v1/generate {prompt, style, duration, callBackUrl}')
msg(ax, 22.5, 15.8, 7.5, '{ taskId: "abc123" }', ret=True)
msg(ax, 15.8, 9.8, 6.7, '{status: PENDING, task_id: "abc123"}', ret=True)
ax.text(16.0, 6.45, '⟳  background polling thread started (every 5 s)', fontsize=5.8, color='#777')

# ── PHASE 4: Persist & Respond ────────────────────────────────────────────────

divider(ax, 7.5, 'PHASE 4 — Persist Result & Redirect', '#fce4ec')
act(ax, 9.8,  7.4, 5.6)
act(ax, 19.0, 7.3, 5.9)

msg(ax, 9.8,  19.0, 7.2, 'repository.update_audio_url(song, result["audio_url"])')
msg(ax, 9.8,  19.0, 6.9, 'repository.update_generation_status(song, COMPLETED)')
msg(ax, 19.0, 9.8, 6.6,  'saved', ret=True)
msg(ax, 9.8,  6.8, 6.3,  'return song', ret=True)
msg(ax, 6.8,  1.2, 6.0,  '302  redirect → /songs/<pk>/', ret=True)

# ── PHASE 5: Async Polling (Suno) ─────────────────────────────────────────────

divider(ax, 5.7, 'PHASE 5 — Async Polling Thread (Suno only)', '#eceff1')

ax.text(12.5, 5.45, '[ background daemon thread — max 60 attempts × 5 s ]',
        fontsize=6.5, color='#555', style='italic')

act(ax, 15.8, 5.3, 2.8)
act(ax, 22.5, 5.1, 4.2)
act(ax, 19.0, 4.5, 3.1)

msg(ax, 15.8, 22.5, 5.0, 'GET /generate/record-info?taskId=abc123')
msg(ax, 22.5, 15.8, 4.6, '{ status: SUCCESS, audioUrl: "https://cdn.suno.ai/…" }', ret=True)
msg(ax, 15.8, 19.0, 4.3, 'song.refresh_from_db()')
msg(ax, 15.8, 19.0, 4.0, 'song.audio_url = audioUrl')
msg(ax, 15.8, 19.0, 3.7, 'song.generation_status = COMPLETED;  song.save()')
msg(ax, 19.0, 15.8, 3.3, 'saved', ret=True)

ax.text(12.0, 2.8,
        '✓  Song is now COMPLETED — browser polls /songs/api/status/<id>/ and shows audio player.',
        fontsize=7, color='#2e7d32', ha='center',
        bbox=dict(boxstyle='round', facecolor='#e8f5e9', alpha=0.8))

os.makedirs('diagrams', exist_ok=True)
plt.tight_layout()
plt.savefig('diagrams/sequence_diagram.png', dpi=150, bbox_inches='tight', facecolor='#fafafa')
plt.close()
print('Saved: diagrams/sequence_diagram.png')
