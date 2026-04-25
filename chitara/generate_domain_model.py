"""
Generates the Chitara domain model UML diagram.
Run: python generate_domain_model.py
Output: diagrams/domain_model.png
"""

import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(figsize=(22, 14))
ax.set_xlim(0, 22)
ax.set_ylim(0, 14)
ax.axis('off')
fig.patch.set_facecolor('#fafafa')


def entity(ax, x, y, w, h, name, attrs, color='#1565c0'):
    ax.add_patch(FancyBboxPatch((x, y + h * 0.55), w, h * 0.45,
        boxstyle='round,pad=0.05', facecolor=color, edgecolor='#222', lw=1.5))
    ax.text(x + w / 2, y + h * 0.77, name, ha='center', va='center',
            fontsize=9, fontweight='bold', color='white')
    ax.add_patch(FancyBboxPatch((x, y), w, h * 0.55,
        boxstyle='round,pad=0.05', facecolor='white', edgecolor='#222', lw=1.5))
    step = h * 0.5 / max(len(attrs), 1)
    for i, a in enumerate(attrs):
        ax.text(x + 0.1, y + h * 0.5 - i * step, a, ha='left', va='top',
                fontsize=6.5, fontfamily='monospace')


def arrow(ax, x1, y1, x2, y2, label='', style='->', color='#444'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle=style, color=color, lw=1.2))
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my + 0.15, label, ha='center', fontsize=6.5,
                color='#333', style='italic')


# ── Entities ─────────────────────────────────────────────────────────────────

entity(ax, 8.5, 10.5, 4.5, 2.8, 'User  (django.auth)', [
    '+ id: AutoField  [PK]',
    '+ username: CharField',
    '+ email: EmailField',
    '+ password: CharField',
], '#37474f')

entity(ax, 0.5, 5.5, 4.5, 4.5, 'Song', [
    '+ id: AutoField  [PK]',
    '+ title: CharField',
    '+ duration: PositiveIntegerField',
    '+ generation_status: CharField',
    '+ audio_url: URLField',
    '+ image_url: URLField',
    '+ external_id: CharField',
    '+ is_shared: BooleanField',
    '+ review_notes: TextField',
    '+ created_at: DateTimeField',
], '#c62828')

entity(ax, 6.0, 6.5, 2.8, 2.2, 'Genre', [
    '+ id: AutoField  [PK]',
    '+ name: CharField',
], '#1565c0')

entity(ax, 9.5, 6.5, 2.8, 2.2, 'Mood', [
    '+ id: AutoField  [PK]',
    '+ name: CharField',
], '#1565c0')

entity(ax, 13.0, 6.5, 2.8, 2.2, 'Occasion', [
    '+ id: AutoField  [PK]',
    '+ name: CharField',
], '#1565c0')

entity(ax, 16.5, 6.5, 4.5, 2.2, 'SingerModel', [
    '+ id: AutoField  [PK]',
    '+ name: CharField',
    '+ description: TextField',
], '#1565c0')

entity(ax, 6.0, 2.5, 2.8, 2.2, 'Theme', [
    '+ id: AutoField  [PK]',
    '+ name: CharField',
], '#1565c0')

entity(ax, 10.0, 2.5, 4.0, 2.8, 'GenerationStatus\n<<TextChoices>>', [
    'PENDING   = "PENDING"',
    'GENERATING= "GENERATING"',
    'COMPLETED = "COMPLETED"',
    'FAILED    = "FAILED"',
], '#4a148c')

entity(ax, 15.5, 2.5, 5.5, 2.8, 'Feedback', [
    '+ id: AutoField  [PK]',
    '+ content: TextField',
    '+ submitted_at: DateTimeField',
    '  user: FK → User',
], '#e65100')

# ── Relationships ─────────────────────────────────────────────────────────────

# User 1 → * Song
ax.annotate('', xy=(2.75, 10.0), xytext=(8.5, 11.2),
    arrowprops=dict(arrowstyle='->', color='#444', lw=1.2))
ax.text(5.5, 10.75, 'owns  1 → *', ha='center', fontsize=7, color='#333', style='italic')

# Song → Genre (FK)
arrow(ax, 5.0, 7.5, 6.0, 7.5, 'genre  * → 1')

# Song → Mood (FK)
ax.annotate('', xy=(9.5, 7.5), xytext=(5.0, 7.2),
    arrowprops=dict(arrowstyle='->', color='#444', lw=1.2))
ax.text(7.3, 7.4, 'mood  * → 1', ha='center', fontsize=7, color='#333', style='italic')

# Song → Occasion (FK)
ax.annotate('', xy=(13.0, 7.2), xytext=(5.0, 6.9),
    arrowprops=dict(arrowstyle='->', color='#444', lw=1.2))
ax.text(9.2, 7.15, 'occasion  * → 1', ha='center', fontsize=7, color='#333', style='italic')

# Song → SingerModel (FK)
ax.annotate('', xy=(16.5, 7.2), xytext=(5.0, 6.6),
    arrowprops=dict(arrowstyle='->', color='#444', lw=1.2))
ax.text(11.0, 7.0, 'singer_model  * → 1', ha='center', fontsize=7, color='#333', style='italic')

# Song ↔ Theme (M2M)
ax.annotate('', xy=(6.0, 3.5), xytext=(2.5, 5.5),
    arrowprops=dict(arrowstyle='<->', color='#555', lw=1.2,
                    connectionstyle='arc3,rad=-0.2'))
ax.text(3.8, 4.3, 'themes  * ↔ *', ha='center', fontsize=7, color='#333', style='italic')

# Song → GenerationStatus (uses)
ax.annotate('', xy=(10.5, 5.3), xytext=(3.5, 5.5),
    arrowprops=dict(arrowstyle='->', color='#999', lw=1.0, linestyle='dashed',
                    connectionstyle='arc3,rad=0.25'))
ax.text(7.3, 5.7, 'generation_status', ha='center', fontsize=6.5, color='#555', style='italic')

# Feedback → User (FK)
ax.annotate('', xy=(13.0, 11.2), xytext=(18.0, 5.3),
    arrowprops=dict(arrowstyle='->', color='#444', lw=1.2,
                    connectionstyle='arc3,rad=-0.2'))
ax.text(16.5, 8.8, 'user  * → 1', ha='center', fontsize=7, color='#333', style='italic')

# ── Title & Legend ────────────────────────────────────────────────────────────

ax.text(11, 13.6, 'Chitara — Domain Model', ha='center',
        fontsize=14, fontweight='bold', color='#1a237e')
ax.text(11, 13.2, 'All entities, attributes, and relationships', ha='center',
        fontsize=9, color='#555')

patches = [
    mpatches.Patch(color='#c62828', label='Core Aggregate'),
    mpatches.Patch(color='#1565c0', label='Lookup / Reference'),
    mpatches.Patch(color='#4a148c', label='Enum  (TextChoices)'),
    mpatches.Patch(color='#37474f', label='External  (Django Auth)'),
    mpatches.Patch(color='#e65100', label='Supporting Entity'),
]
ax.legend(handles=patches, loc='lower right', fontsize=7.5, framealpha=0.9)

os.makedirs('diagrams', exist_ok=True)
plt.tight_layout()
plt.savefig('diagrams/domain_model.png', dpi=150, bbox_inches='tight', facecolor='#fafafa')
plt.close()
print('Saved: diagrams/domain_model.png')
