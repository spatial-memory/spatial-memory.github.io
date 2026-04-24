import matplotlib.pyplot as plt
import matplotlib
import matplotlib.patches as mpatches
import numpy as np

matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.size'] = 13
outdir = '/tmp/spatial-memory-survey/docs/static/images/'

# ============================================================
# 1. Evolution / Teaser figure
# ============================================================
fig, ax = plt.subplots(figsize=(10, 7))
ax.set_xlabel('Memory Efficiency', fontsize=15, fontweight='bold')
ax.set_ylabel('Geometric Completeness', fontsize=15, fontweight='bold')
ax.set_xlim(0, 10)
ax.set_ylim(0, 8.5)
ax.set_xticks([])
ax.set_yticks([])
ax.text(0.5, 0.2, 'Low', fontsize=11, color='gray')
ax.text(9.0, 0.2, 'High', fontsize=11, color='gray')
ax.text(0.1, 0.8, 'Low', fontsize=11, color='gray', rotation=90)
ax.text(0.1, 7.2, 'High', fontsize=11, color='gray', rotation=90)

# Ideal star
ax.plot(9.2, 8.0, marker='*', markersize=20, color='#D4A843', zorder=10)
ax.text(8.4, 8.0, 'Ideal', fontsize=12, fontweight='bold', color='#D4A843', va='center')

# Paradigm boxes
boxes = [
    (2.0, 6.8, 'Dense Grids\nGB / building', '#2B6CB0', '#2B6CB020'),
    (4.8, 2.0, 'Sparse Features\n55 MB, no geometry', '#D4A843', '#D4A84320'),
    (5.2, 5.6, 'Neural / 3DGS\n8 MB map; 1.3 GB GPU', '#6B46C1', '#6B46C120'),
    (8.4, 4.2, 'Scene Graphs\n48 MB, semantic', '#006747', '#00674720'),
]
for x, y, text, color, facecolor in boxes:
    bbox = dict(boxstyle='round,pad=0.5', facecolor=facecolor, edgecolor=color, linewidth=2)
    ax.text(x, y, text, fontsize=11, ha='center', va='center', bbox=bbox, fontweight='bold')

# Arrows
arrow_kw = dict(arrowstyle='->', lw=2.5, mutation_scale=15)
ax.annotate('', xy=(4.0, 2.0), xytext=(2.0, 5.8), arrowprops=dict(**arrow_kw, color='#2B6CB080'))
ax.annotate('', xy=(5.0, 4.6), xytext=(4.8, 3.0), arrowprops=dict(**arrow_kw, color='#6B46C180'))
ax.annotate('', xy=(7.8, 4.8), xytext=(6.2, 5.6), arrowprops=dict(**arrow_kw, color='#00674780'))

# Era labels
for i, (color, label) in enumerate([('#2B6CB0', '1990s-2010s'), ('#6B46C1', '2020-2023'), ('#006747', '2023-2025')]):
    ax.plot(1.0, 1.5 - i*0.45, 'o', color=color, markersize=10)
    ax.text(1.3, 1.5 - i*0.45, label, fontsize=10, va='center', fontweight='bold', color=color)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig(outdir + 'evolution.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print('Saved evolution.png')

# ============================================================
# 2. Alpha comparison bar chart
# ============================================================
fig, ax = plt.subplots(figsize=(10, 5))
systems = ['Point-SLAM', 'Basalt', 'ORB-SLAM3', 'SplaTAM', 'Co-SLAM', 'SGS-SLAM', 'NICE-SLAM']
alphas = [2.3, 3.4, 4.0, 55, 157, 159, 215]
colors = ['#228B22', '#228B22', '#228B22', '#D4A843', '#CC2222', '#CC2222', '#CC2222']

bars = ax.barh(systems, alphas, color=colors, edgecolor='white', height=0.6)
ax.set_xlabel('Overhead Factor (α)', fontsize=14, fontweight='bold')
ax.set_xlim(0, 240)
ax.invert_yaxis()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='x', alpha=0.2)

for bar, val in zip(bars, alphas):
    ax.text(bar.get_width() + 3, bar.get_y() + bar.get_height()/2,
            f'{val}', va='center', fontweight='bold', fontsize=12)

plt.tight_layout()
plt.savefig(outdir + 'alpha_comparison.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print('Saved alpha_comparison.png')

# ============================================================
# 3. Memory bottleneck (Jetson budget bars)
# ============================================================
fig, ax = plt.subplots(figsize=(10, 4))

systems = ['ORB-SLAM3', 'Co-SLAM', 'SplaTAM']
used = [0.22, 1.3, 14.0]
map_sizes = ['55 MB', '8 MB', '254 MB']
remaining = [15.78, 14.7, 2.0]
colors_used = ['#228B22', '#D4A843', '#CC2222']

y_pos = [2, 1, 0]
for i, (sys, u, r, c) in enumerate(zip(systems, used, remaining, colors_used)):
    ax.barh(y_pos[i], u, color=c, height=0.5, label=sys if i == 0 else None)
    ax.barh(y_pos[i], r, left=u, color='#E8E8E8', height=0.5)
    if u > 1:
        ax.text(u/2, y_pos[i], f'{u} GB runtime', ha='center', va='center', fontweight='bold',
                color='white', fontsize=10)
    else:
        ax.text(u + 0.3, y_pos[i], f'{u} GB runtime', ha='left', va='center', fontweight='bold',
                color=c, fontsize=10)

ax.set_yticks(y_pos)
ax.set_yticklabels([f'{s}\n(map: {m})' for s, m in zip(systems, map_sizes)], fontsize=11, fontweight='bold')
ax.set_xlabel('Memory (GB)', fontsize=13, fontweight='bold')
ax.set_xlim(0, 16)
ax.set_xticks([0, 4, 8, 12, 16])
ax.axvline(x=16, color='#8A1538', linewidth=2, linestyle='--', alpha=0.7)
ax.text(16.1, 2.5, '16 GB\nbudget', fontsize=10, color='#8A1538', fontweight='bold', va='center')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='x', alpha=0.15)

plt.tight_layout()
plt.savefig(outdir + 'memory_bottleneck.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print('Saved memory_bottleneck.png')

# ============================================================
# 4. Profiling table as image
# ============================================================
fig, ax = plt.subplots(figsize=(12, 6))
ax.axis('off')

col_labels = ['System', 'Paradigm', 'ATE (cm)', 'PSNR (dB)', 'Map (MB)', 'Peak (MB)', 'FPS', 'α']
cell_data = [
    ['', 'Sparse — EuRoC (real-world)', '', '', '', '', '', ''],
    ['ORB-SLAM3', 'Sparse', '3.5', '—', '55', '220', '30', '4.0'],
    ['Basalt', 'Sparse (VI)', '8.8', '—', '35', '120', '30', '~3.4'],
    ['VINS-Mono', 'Sparse (VI)', '10.6', '—', '40', '—', '20', '—'],
    ['', 'Neural — Replica (synthetic, RGB-D)', '', '', '', '', '', ''],
    ['iMAP', 'NeRF', '3.12', '22.1', '1', '—', '3', '—'],
    ['NICE-SLAM', 'NeRF', '1.06', '24.4', '47', '10,082', '2', '215'],
    ['Co-SLAM', 'NeRF', '1.00', '30.2', '8', '1,258', '16', '157'],
    ['Point-SLAM', 'NeRF', '0.52', '35.2', '2,865', '6,563', '1', '2.3'],
    ['SplaTAM', '3DGS', '0.36', '34.1', '254', '14,024', '—', '55'],
    ['MonoGS', '3DGS', '0.58', '38.9', '90', '—', '3', '—'],
    ['GS-SLAM', '3DGS', '0.50', '34.3', '198', '—', '8', '—'],
    ['SGS-SLAM', '3DGS (Sem.)', '0.41', '34.7', '254', '40,330', '2', '159'],
]

table = ax.table(cellText=cell_data, colLabels=col_labels, loc='center', cellLoc='center')
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 1.4)

# Style header
for j in range(len(col_labels)):
    cell = table[0, j]
    cell.set_facecolor('#8A1538')
    cell.set_text_props(color='white', fontweight='bold')

# Style group headers
for row_idx in [1, 5]:
    for j in range(len(col_labels)):
        cell = table[row_idx, j]
        cell.set_facecolor('#F0F0F0')
        cell.set_text_props(fontweight='bold', fontstyle='italic')

# Color alpha cells
alpha_colors = {
    '4.0': '#228B22', '~3.4': '#228B22', '2.3': '#228B22',
    '55': '#D4A843', '157': '#CC2222', '159': '#CC2222', '215': '#CC2222'
}
for i in range(1, len(cell_data) + 1):
    alpha_val = table[i, 7].get_text().get_text()
    if alpha_val in alpha_colors:
        table[i, 7].set_text_props(color=alpha_colors[alpha_val], fontweight='bold')

plt.title('Unified Efficiency Analysis Across Spatial Memory Paradigms',
          fontsize=14, fontweight='bold', color='#8A1538', pad=20)
plt.tight_layout()
plt.savefig(outdir + 'profiling_table.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print('Saved profiling_table.png')

# ============================================================
# 5. Selection guide table as image
# ============================================================
fig, ax = plt.subplots(figsize=(10, 4))
ax.axis('off')

col_labels = ['Constraint', 'Recommended', 'α range', 'Type', 'Max Map', 'Avoid']
cell_data = [
    ['CPU-only (<8 GB)', 'Sparse, Octree', '3–5', 'CPU', '~4 GB', 'Neural'],
    ['Embedded GPU (<16 GB)', 'Sparse, SG', '4–10', 'CPU', '~2 GB', 'Raw 3DGS'],
    ['Dense geometry', 'TSDF, 3DGS', '~55', 'GPU', '290 MB', 'Sparse only'],
    ['Photo rendering', '3DGS, NeRF', '2–215', 'GPU', '75 MB', 'Occupancy'],
    ['Multi-hour', 'Submaps, Stream', 'varies', '—', '—', 'Monolithic'],
    ['Semantic', 'SG, VLM', '4–10', 'CPU', '—', 'Geom. only'],
]

row_colors = ['#E8F5E9', '#E8F5E9', '#FFF3E0', '#FFEBEE', '#F5F5F5', '#F5F5F5']

table = ax.table(cellText=cell_data, colLabels=col_labels, loc='center', cellLoc='center')
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 1.5)

for j in range(len(col_labels)):
    cell = table[0, j]
    cell.set_facecolor('#8A1538')
    cell.set_text_props(color='white', fontweight='bold')

for i, color in enumerate(row_colors):
    for j in range(len(col_labels)):
        table[i+1, j].set_facecolor(color)

plt.title('Representation Selection Guide by Primary Constraint',
          fontsize=13, fontweight='bold', color='#8A1538', pad=20)
plt.tight_layout()
plt.savefig(outdir + 'selection_guide.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print('Saved selection_guide.png')

# ============================================================
# 6. Checkpoint discrepancy chart
# ============================================================
fig, ax = plt.subplots(figsize=(9, 5))
systems = ['Co-SLAM', 'NICE-SLAM', 'Point-SLAM', 'SplaTAM', 'SGS-SLAM']
ours = [8, 47, 2865, 254, 254]
lit = [32, 235, 80, 85, 92]

x = np.arange(len(systems))
w = 0.35
bars1 = ax.bar(x - w/2, ours, w, label='Ours (measured)', color='#8A1538', edgecolor='white')
bars2 = ax.bar(x + w/2, lit, w, label='Literature', color='#D4A843', edgecolor='white')

ax.set_ylabel('Checkpoint Size (MB)', fontsize=13, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(systems, fontsize=11, fontweight='bold')
ax.set_yscale('log')
ax.legend(fontsize=11, framealpha=0.9)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='y', alpha=0.2)

for bar, val in zip(bars1, ours):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.15,
            f'{val}', ha='center', fontsize=9, fontweight='bold', color='#8A1538')
for bar, val in zip(bars2, lit):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.15,
            f'{val}', ha='center', fontsize=9, fontweight='bold', color='#D4A843')

plt.tight_layout()
plt.savefig(outdir + 'checkpoint_discrepancy.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print('Saved checkpoint_discrepancy.png')

print('\nAll figures generated!')
