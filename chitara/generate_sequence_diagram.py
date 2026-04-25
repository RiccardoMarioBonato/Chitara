"""
Chitara Sequence Diagram — Dark Theme
Run: python generate_sequence_diagram.py
Output: diagrams/sequence_diagram.png
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BG    = '#0d0d0d'
FIG_W = 28
FIG_H = 20

ACTORS = [
    (1.5,  'User\n(Browser)',             '#1e3a5f', '#3b82f6'),
    (4.8,  'Song\nGenerationView',         '#14532d', '#22c55e'),
    (8.1,  'Song\nPreviewView',            '#14532d', '#22c55e'),
    (11.4, 'Song\nGeneration\nService',    '#7c2d12', '#f97316'),
    (14.7, 'Strategy\nFactory',            '#12104a', '#818cf8'),
    (18.0, 'Mock / Suno\nStrategy',        '#3b0764', '#a855f7'),
    (21.3, 'Song\nRepository',             '#7f1d1d', '#ef4444'),
    (24.6, 'Suno API\n(External)',          '#1a1a1a', '#6b7280'),
]

ACTOR_W = 2.4
ACTOR_H = 1.0


def draw_actors(ax):
    for x, name, bg, border in ACTORS:
        ax.add_patch(plt.Rectangle(
            (x - ACTOR_W/2, FIG_H - ACTOR_H - 0.3),
            ACTOR_W, ACTOR_H,
            facecolor=bg, edgecolor=border, lw=1.3, zorder=3
        ))
        ax.text(x, FIG_H - ACTOR_H/2 - 0.3, name,
                ha='center', va='center',
                fontsize=6.2, fontweight='bold', color='white',
                multialignment='center', zorder=4)
        ax.plot([x, x], [FIG_H - ACTOR_H - 0.3, 0.4],
                color='#333', lw=0.9, linestyle='--', zorder=1)


def msg(ax, x1, x2, y, label, ret=False, color='#9ca3af'):
    style  = '<-' if ret else '->'
    lcolor = '#5b5b7a' if ret else color
    ax.annotate('', xy=(x2, y), xytext=(x1, y),
        arrowprops=dict(arrowstyle=style, color=lcolor, lw=1.0), zorder=2)
    mid = (x1 + x2) / 2
    max_c = 38
    disp  = label if len(label) <= max_c else label[:max_c-1] + '…'
    ax.text(mid, y + 0.1, disp,
            ha='center', va='bottom', fontsize=5.8,
            color='#c8c8d8' if not ret else '#7070a0', zorder=4)


def activation(ax, x, y_top, y_bot, color='#2a2a3a'):
    ax.add_patch(plt.Rectangle(
        (x - 0.12, y_bot), 0.24, y_top - y_bot,
        facecolor=color, edgecolor='#555', lw=0.7, zorder=2
    ))


def phase_label(ax, y, label, color='#1a1a2e'):
    ax.add_patch(plt.Rectangle(
        (0.2, y - 0.2), FIG_W - 0.4, 0.4,
        facecolor=color, edgecolor='#333', lw=0.5, alpha=0.7, zorder=1
    ))
    ax.text(0.4, y, label, ha='left', va='center',
            fontsize=6.8, fontweight='bold', color='#9ca3af', zorder=4)


fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.set_facecolor(BG)
fig.patch.set_facecolor(BG)
ax.axis('off')

draw_actors(ax)

U   = ACTORS[0][0]
V1  = ACTORS[1][0]
V2  = ACTORS[2][0]
SV  = ACTORS[3][0]
SF  = ACTORS[4][0]
ST  = ACTORS[5][0]
SR  = ACTORS[6][0]
API = ACTORS[7][0]

# ── PHASE 1 ───────────────────────────────────────────────────────────────────
phase_label(ax, 17.8, 'PHASE 1 — Generation Form')
msg(ax, U,  V1, 17.4, 'GET /songs/generate/')
msg(ax, V1, U,  17.0, '200 SongGenerationForm', ret=True)
msg(ax, U,  V1, 16.6, 'POST /songs/generate/ {title, genre, mood}')
activation(ax, V1, 16.6, 16.0)
msg(ax, V1, V2, 16.2, 'store form_data in session')
msg(ax, V1, U,  15.8, '302 redirect -> /generate/preview/', ret=True)

# ── PHASE 2 ───────────────────────────────────────────────────────────────────
phase_label(ax, 15.4, 'PHASE 2 — Preview (GEN-4 SRS)')
msg(ax, U,  V2, 15.0, 'GET /songs/generate/preview/')
activation(ax, V2, 15.0, 14.3)
msg(ax, V2, U,  14.6, '200 song_preview.html (summary)', ret=True)
msg(ax, U,  V2, 14.2, 'POST /songs/generate/preview/ (Confirm)')

# ── PHASE 3 ───────────────────────────────────────────────────────────────────
phase_label(ax, 13.8, 'PHASE 3 — Strategy Dispatch')
activation(ax, V2, 14.2, 12.8)
activation(ax, SV, 13.6, 11.0)
msg(ax, V2, SV, 13.5, 'service.generate_song(user, form_data)')
msg(ax, SV, SR, 13.2, 'repository.save(song) -> status=PENDING')
activation(ax, SR, 13.2, 12.9)
msg(ax, SR, SV, 12.9, 'song (PK assigned)', ret=True)
msg(ax, SV, SF, 12.6, 'StrategyFactory.get_strategy()')
activation(ax, SF, 12.6, 12.3)
msg(ax, SF, SV, 12.3, 'MockStrategy OR SunoStrategy', ret=True)

ax.text(16.5, 12.1, '[ GENERATOR_STRATEGY = mock ]',
        fontsize=6, color='#c084fc', style='italic',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#1a0a2e',
                  edgecolor='#a855f7', alpha=0.7), zorder=4)

msg(ax, SV, ST, 11.8, 'strategy.generate(song_request)')
activation(ax, ST, 11.8, 11.2)
msg(ax, ST, SV, 11.2, '{status:SUCCESS, audio_url:...}', ret=True)

ax.text(16.5, 10.9, '[ GENERATOR_STRATEGY = suno ]',
        fontsize=6, color='#818cf8', style='italic',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#0a0a2e',
                  edgecolor='#818cf8', alpha=0.7), zorder=4)

msg(ax, SV, ST, 10.6, 'strategy.generate(song_request, song)')
activation(ax, ST, 10.6, 9.5)
msg(ax, ST, API, 10.3, 'POST /api/v1/generate {prompt, style}')
activation(ax, API, 10.3, 9.8)
msg(ax, API, ST, 9.8, '{taskId: "abc123"}', ret=True, color='#6b7280')
msg(ax, ST, SV, 9.5, '{status:PENDING, task_id:"abc123"}', ret=True)

# ── PHASE 4 ───────────────────────────────────────────────────────────────────
phase_label(ax, 9.2, 'PHASE 4 — Persist & Respond')
activation(ax, SV, 9.2, 8.0)
activation(ax, SR, 9.0, 8.2)
msg(ax, SV, SR, 8.9, 'update_audio_url(song, result.audio_url)')
msg(ax, SV, SR, 8.6, 'update_generation_status(COMPLETED)')
msg(ax, SR, SV, 8.3, 'saved', ret=True)
msg(ax, SV, V2, 8.0, 'return song', ret=True)
msg(ax, V2, U,  7.7, '302 redirect -> /songs/<pk>/', ret=True)

ax.text(17.0, 7.4,
        'Background polling thread started (Suno only)',
        fontsize=6, color='#9ca3af', zorder=4)

# ── PHASE 5 ───────────────────────────────────────────────────────────────────
phase_label(ax, 7.1, 'PHASE 5 — Async Polling Thread (Suno only)')

ax.text(14.0, 6.8, '[ background daemon thread — max 60 attempts x 5s ]',
        ha='center', fontsize=6, color='#7070a0', style='italic', zorder=4)

activation(ax, ST, 6.6, 4.2)
activation(ax, API, 6.4, 5.6)
activation(ax, SR, 5.8, 5.0)
msg(ax, ST, API, 6.3, 'GET /generate/record-info?taskId=abc123')
msg(ax, API, ST, 5.9, '{status:SUCCESS, audioUrl:"cdn..."}', ret=True)
msg(ax, ST, SR, 5.6, 'song.refresh_from_db()')
msg(ax, ST, SR, 5.3, 'song.audio_url = audioUrl')
msg(ax, ST, SR, 5.0, 'song.status = COMPLETED; save()')
msg(ax, SR, ST, 4.7, 'saved', ret=True)

ax.text(FIG_W/2, 4.2,
        'Song is playable — browser polls /songs/api/status/<id>/ and shows audio player',
        ha='center', fontsize=7, color='#22c55e',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='#0a2e0a',
                  edgecolor='#22c55e', alpha=0.7), zorder=4)

# ── TITLE ─────────────────────────────────────────────────────────────────────
ax.text(FIG_W/2, FIG_H - 0.2, 'Chitara — Song Generation Sequence Diagram',
        ha='center', fontsize=14, fontweight='bold', color='white')
ax.text(FIG_W/2, FIG_H - 0.55,
        'Form -> Preview -> Confirm -> Strategy Dispatch (Mock / Suno) -> DB Persist',
        ha='center', fontsize=8, color='#9ca3af')

os.makedirs('diagrams', exist_ok=True)
plt.tight_layout(pad=0.2)
plt.savefig('diagrams/sequence_diagram.png', dpi=150,
            bbox_inches='tight', facecolor=BG)
plt.close()
print('Saved: diagrams/sequence_diagram.png')
