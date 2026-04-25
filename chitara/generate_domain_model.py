"""
Chitara Domain Model — Dark Theme
Run: python generate_domain_model.py
Output: diagrams/domain_model.png
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

BG     = '#0d0d0d'
FIG_W  = 26
FIG_H  = 16

COLORS = {
    'core':     ('#4a0a0a', '#ef4444'),
    'lookup':   ('#0a1a3a', '#3b82f6'),
    'enum':     ('#2d0a4e', '#a855f7'),
    'auth':     ('#1a1a1a', '#6b7280'),
    'support':  ('#3a1a00', '#f97316'),
}


def entity(ax, x, y, w, name, attrs, kind='core', stereotype=None,
           title_fs=8.0, attr_fs=6.5, line_h=0.28, pad=0.2):
    bg, border = COLORS[kind]
    n      = len(attrs)
    body_h = max(0.4, n * line_h + pad * 2)
    hdr_h  = 0.5 if stereotype else 0.42
    total  = hdr_h + body_h

    ax.add_patch(plt.Rectangle((x, y+body_h), w, hdr_h,
        facecolor=border, edgecolor='none', zorder=2))
    ax.add_patch(plt.Rectangle((x, y), w, body_h,
        facecolor=bg, edgecolor=border, lw=1.5, zorder=2))
    ax.add_patch(plt.Rectangle((x, y), w, total,
        facecolor='none', edgecolor=border, lw=1.5, zorder=3))

    ty = y + body_h + hdr_h
    if stereotype:
        ax.text(x+w/2, ty-0.15, f'«{stereotype}»', ha='center', va='top',
                fontsize=5.5, color='white', alpha=0.85, zorder=4)
        ax.text(x+w/2, ty-0.35, name, ha='center', va='top',
                fontsize=title_fs, fontweight='bold', color='white', zorder=4)
    else:
        ax.text(x+w/2, ty-0.24, name, ha='center', va='top',
                fontsize=title_fs, fontweight='bold', color='white', zorder=4)

    for i, attr in enumerate(attrs):
        ay    = y + body_h - pad - i * line_h
        max_c = int(w / 0.085)
        disp  = attr if len(attr) <= max_c else attr[:max_c-1] + '…'
        ax.text(x+0.12, ay, disp, ha='left', va='top',
                fontsize=attr_fs, color='#c8c8d8',
                fontfamily='monospace', zorder=4)
    return total


def rel(ax, x1, y1, x2, y2, label='', mult1='', mult2='',
        color='#6b7280', style='->'):
    dashed = style.startswith('--')
    real_style = '->' if dashed else style
    props = dict(arrowstyle=real_style, color=color, lw=1.1)
    if dashed:
        props['linestyle'] = 'dashed'
    ax.annotate('', xy=(x2,y2), xytext=(x1,y1),
        arrowprops=props, zorder=1)
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx, my+0.14, label, ha='center', fontsize=6,
                color='#9ca3af', style='italic', zorder=4)
    if mult1:
        ax.text(x1+0.15, y1+0.12, mult1, fontsize=6, color='#9ca3af', zorder=4)
    if mult2:
        ax.text(x2+0.15, y2+0.12, mult2, fontsize=6, color='#9ca3af', zorder=4)


fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.set_facecolor(BG)
fig.patch.set_facecolor(BG)
ax.axis('off')

# ── ENTITIES ─────────────────────────────────────────────────────────────────

entity(ax, 10.0, 12.5, 5.0, 'User (django.auth)', [
    '+ id: AutoField [PK]',
    '+ username: CharField',
    '+ email: EmailField',
    '+ password: CharField',
], kind='auth')

entity(ax, 0.5, 7.5, 4.8, 'Song', [
    '+ id: AutoField [PK]',
    '+ title: CharField(100)',
    '+ duration: PositiveIntegerField',
    '+ generation_status: CharField',
    '+ audio_url: URLField',
    '+ image_url: URLField',
    '+ external_id: CharField',
    '+ is_shared: BooleanField',
    '+ review_notes: TextField',
    '+ created_at: DateTimeField',
], kind='core')

entity(ax, 6.5, 9.0, 3.2, 'Genre', ['+ id: AutoField [PK]', '+ name: CharField'], kind='lookup')
entity(ax, 10.5, 9.0, 3.2, 'Mood',  ['+ id: AutoField [PK]', '+ name: CharField'], kind='lookup')
entity(ax, 14.5, 9.0, 3.2, 'Occasion', ['+ id: AutoField [PK]', '+ name: CharField'], kind='lookup')
entity(ax, 18.5, 9.0, 4.0, 'SingerModel', [
    '+ id: AutoField [PK]',
    '+ name: CharField',
    '+ description: TextField',
], kind='lookup')

entity(ax, 6.5, 6.5, 3.2, 'Theme', ['+ id: AutoField [PK]', '+ name: CharField'], kind='lookup')

entity(ax, 10.5, 5.5, 4.5, 'GenerationStatus', [
    'PENDING    = "PENDING"',
    'GENERATING = "GENERATING"',
    'COMPLETED  = "COMPLETED"',
    'FAILED     = "FAILED"',
], kind='enum', stereotype='TextChoices')

entity(ax, 17.0, 6.5, 5.5, 'Feedback', [
    '+ id: AutoField [PK]',
    '+ content: TextField',
    '+ submitted_at: DateTimeField',
    '+ user: FK -> User',
], kind='support')

# ── RELATIONSHIPS ─────────────────────────────────────────────────────────────
rel(ax, 10.0, 13.5, 5.3, 11.2, 'owns', '1', '*', color='#6b7280')
rel(ax, 5.3, 9.5, 6.5, 9.5, 'genre FK', '*', '1')
rel(ax, 5.3, 9.2, 10.5, 9.2, 'mood FK', '*', '1')
rel(ax, 5.3, 9.0, 14.5, 9.0, 'occasion FK', '*', '1')
rel(ax, 5.3, 8.8, 18.5, 9.0, 'singer_model FK', '*', '1')
rel(ax, 2.5, 7.5, 6.5, 7.8, 'themes M2M', '*', '*')
rel(ax, 3.5, 7.5, 11.5, 7.3, 'uses', color='#6b7280', style='-->')
rel(ax, 15.0, 12.5, 20.0, 8.2, 'user FK', '*', '1')

# ── TITLE ─────────────────────────────────────────────────────────────────────
ax.text(FIG_W/2, FIG_H-0.35, 'Chitara — Domain Model',
        ha='center', fontsize=14, fontweight='bold', color='white')
ax.text(FIG_W/2, FIG_H-0.75, 'All entities and relationships',
        ha='center', fontsize=8.5, color='#9ca3af')

legend_items = [
    mpatches.Patch(color='#ef4444', label='Core Aggregate (Song)'),
    mpatches.Patch(color='#3b82f6', label='Lookup / Reference'),
    mpatches.Patch(color='#a855f7', label='Enum (TextChoices)'),
    mpatches.Patch(color='#6b7280', label='External (Django Auth)'),
    mpatches.Patch(color='#f97316', label='Supporting Entity'),
]
ax.legend(handles=legend_items, loc='lower right', fontsize=7,
          framealpha=0.2, facecolor='#1a1a1a', edgecolor='#444',
          labelcolor='white', bbox_to_anchor=(0.99, 0.01))

os.makedirs('diagrams', exist_ok=True)
plt.tight_layout(pad=0.3)
plt.savefig('diagrams/domain_model.png', dpi=150,
            bbox_inches='tight', facecolor=BG)
plt.close()
print('Saved: diagrams/domain_model.png')
