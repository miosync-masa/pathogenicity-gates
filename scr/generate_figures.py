#!/usr/bin/env python3
"""
p53 Gate & Channel v17 — Manuscript Figure Generation
=====================================================
Fig 1: Framework overview (conceptual SVG)
Fig 2: Gate taxonomy and symmetry (conceptual SVG)
Fig 3: Full-length benchmark (data)
Fig 4: IDR discoveries (data + annotation)
Fig 5: False negatives as missing physics map
Fig 6: ClinVar vs molecular mechanism resolution
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np
import json
import os

# Style
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 10,
    'axes.linewidth': 0.8,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.2,
})

OUTDIR = '/mnt/user-data/outputs/figures'
os.makedirs(OUTDIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════
# Fig 3: Full-length benchmark
# ═══════════════════════════════════════════════════════════
def fig3_benchmark():
    fig, axes = plt.subplots(1, 3, figsize=(14, 5), gridspec_kw={'width_ratios': [2, 3, 1.5]})

    # Panel A: Global metrics
    ax = axes[0]
    metrics = ['Sensitivity', 'Specificity', 'PPV', 'NPV']
    values = [80.8, 52.2, 89.1, 36.1]
    adj_values = [81.3, 59.8, 92.0, 36.1]  # molecular-adjusted
    x = np.arange(len(metrics))
    w = 0.35
    bars1 = ax.bar(x - w/2, values, w, label='ClinVar labels', color='#4A90D9', edgecolor='white')
    bars2 = ax.bar(x + w/2, adj_values, w, label='Molecular-adjusted', color='#E8853D', edgecolor='white')
    ax.set_ylabel('Percentage (%)')
    ax.set_xticks(x)
    ax.set_xticklabels(metrics, rotation=30, ha='right')
    ax.set_ylim(0, 100)
    ax.legend(fontsize=8, loc='upper right')
    ax.set_title('A. Global Performance', fontweight='bold', fontsize=11)
    # Add value labels
    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5,
                f'{bar.get_height():.1f}', ha='center', va='bottom', fontsize=7)
    for bar in bars2:
        if bar.get_height() != bars1[list(bars2).index(bar)].get_height():
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5,
                    f'{bar.get_height():.1f}', ha='center', va='bottom', fontsize=7, color='#E8853D')

    # Panel B: Per-region breakdown
    ax = axes[1]
    regions = ['Core\n(94-289)', 'Tet\n(325-356)', 'TAD1\n(1-40)', 'TAD2\n(41-61)',
               'PRD\n(62-93)', 'Linker\n(290-324)', 'CTD\n(357-393)']
    sens = [90.9, 67.5, 57.9, 23.8, 66.7, 41.9, 70.6]
    spec = [42.5, 38.9, 54.5, 77.8, 64.7, 68.2, 41.2]
    n_var = [821, 106, 89, 57, 98, 99, 99]

    x = np.arange(len(regions))
    colors_sens = ['#2E5090']*2 + ['#7FB069']*5  # structured=blue, IDR=green
    colors_spec = ['#6B8EBF']*2 + ['#B5D99C']*5

    bars_s = ax.bar(x - 0.2, sens, 0.35, color=colors_sens, edgecolor='white', label='Sensitivity')
    bars_p = ax.bar(x + 0.2, spec, 0.35, color=colors_spec, edgecolor='white', label='Specificity')

    ax.set_ylabel('Percentage (%)')
    ax.set_xticks(x)
    ax.set_xticklabels(regions, fontsize=8)
    ax.set_ylim(0, 105)
    ax.axhline(y=90.9, color='#2E5090', linestyle='--', alpha=0.3, linewidth=0.8)
    ax.legend(fontsize=8)
    ax.set_title('B. Per-Region Performance', fontweight='bold', fontsize=11)

    # N annotations
    for i, n in enumerate(n_var):
        ax.text(i, max(sens[i], spec[i]) + 3, f'n={n}', ha='center', fontsize=6, color='gray')

    # Structured vs IDR labels
    ax.annotate('Structured (3D)', xy=(0.5, -0.18), xycoords=('data', 'axes fraction'),
                fontsize=8, ha='center', color='#2E5090', fontweight='bold')
    ax.annotate('IDR (1D gates)', xy=(4, -0.18), xycoords=('data', 'axes fraction'),
                fontsize=8, ha='center', color='#7FB069', fontweight='bold')

    # Panel C: Hotspots
    ax = axes[2]
    hotspot_names = ['R175H', 'C176F', 'H179R', 'Y220C', 'G245S',
                     'R248W', 'R249S', 'R273H', 'R280K']
    caught = [1]*9  # all caught
    colors_h = ['#2E5090' if c else '#FFB3B3' for c in caught]
    ax.barh(range(len(hotspot_names)), caught, color=colors_h, edgecolor='white')
    ax.set_yticks(range(len(hotspot_names)))
    ax.set_yticklabels(hotspot_names, fontsize=8, fontfamily='monospace')
    ax.set_xlim(0, 1.3)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(['Miss', 'Catch'])
    ax.set_title('C. Hotspots\n9/9', fontweight='bold', fontsize=11)
    ax.invert_yaxis()

    plt.tight_layout()
    plt.savefig(f'{OUTDIR}/fig3_benchmark.pdf')
    plt.savefig(f'{OUTDIR}/fig3_benchmark.png')
    plt.close()
    print("Fig 3: done")

# ═══════════════════════════════════════════════════════════
# Fig 4: IDR discoveries
# ═══════════════════════════════════════════════════════════
def fig4_idr_discoveries():
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Panel A: Proline-directed kinase [S/T]-P
    ax = axes[0, 0]
    motifs = ['S33-P34\n(CDK5/7)', 'S46-P47\n(CDK5/DYRK2)', 'S315-P316\n(CDK1/2)']
    path_counts = [4, 2, 2]  # pathogenic Pro→X variants
    benign_counts = [0, 1, 1]  # P47S, P316T
    x = np.arange(len(motifs))
    ax.bar(x - 0.15, path_counts, 0.3, color='#D94A4A', label='Pathogenic', edgecolor='white')
    ax.bar(x + 0.15, benign_counts, 0.3, color='#4A90D9', label='Benign*', edgecolor='white')
    ax.set_ylabel('Pro→X variants')
    ax.set_xticks(x)
    ax.set_xticklabels(motifs, fontsize=9)
    ax.set_title('A. Proline-Directed Kinase [S/T]-P Motifs', fontweight='bold', fontsize=11)
    ax.legend(fontsize=8)
    ax.annotate('*P47S: biochemically confirmed\n phospho reduction (molecular TP)',
                xy=(1, 1), fontsize=7, style='italic', color='gray')

    # Panel B: PPII spacer gate effect on PRD
    ax = axes[0, 1]
    labels = ['v16\n(no IDR)', 'v17 initial\n(Gate A only)', 'v17 final\n(Gate A + A2)']
    prd_sens = [0, 40.0, 66.7]  # v16 had no PRD coverage
    prd_spec = [0, 82.4, 64.7]
    x = np.arange(len(labels))
    ax.bar(x - 0.15, prd_sens, 0.3, color='#D94A4A', label='Sensitivity', edgecolor='white')
    ax.bar(x + 0.15, prd_spec, 0.3, color='#4A90D9', label='Specificity', edgecolor='white')
    ax.set_ylabel('Percentage (%)')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(0, 100)
    ax.set_title('B. PRD Coverage: PPII Gate Evolution', fontweight='bold', fontsize=11)
    ax.legend(fontsize=8)
    ax.annotate('+26.7pp', xy=(2, 66.7), xytext=(2.3, 80),
                arrowprops=dict(arrowstyle='->', color='#D94A4A'),
                fontsize=10, color='#D94A4A', fontweight='bold')

    # Panel C: Ch7 MECE split effect
    ax = axes[1, 0]
    categories = ['Core Sens\n(90.9%)', 'Tet Sens\n(67.5%)']
    v16_vals = [90.9, 65.2]
    v17_broken = [89.4, 52.2]  # before MECE fix
    v17_fixed = [90.9, 67.5]   # after MECE fix (325-356)
    x = np.arange(len(categories))
    w = 0.25
    ax.bar(x - w, v16_vals, w, color='#2E5090', label='v16 baseline', edgecolor='white')
    ax.bar(x,     v17_broken, w, color='#FFB3B3', label='v17 naive (AND logic)', edgecolor='white')
    ax.bar(x + w, v17_fixed, w, color='#7FB069', label='v17 MECE (OR logic)', edgecolor='white')
    ax.set_ylabel('Sensitivity (%)')
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_ylim(40, 100)
    ax.set_title('C. Ch7 PTM MECE Split: Zero Fallback', fontweight='bold', fontsize=11)
    ax.legend(fontsize=7, loc='lower right')
    ax.annotate('7 fallbacks\neliminated', xy=(0.5, 90.9), fontsize=8,
                color='#7FB069', fontweight='bold', ha='center')

    # Panel D: Gate B IDR Gly examples
    ax = axes[1, 1]
    examples = [
        ('G360V', 'Path', 'G→V: +79.9 Å³\nbackbone constrained'),
        ('G360R', 'Path', 'G→R: +113.3 Å³\n+ charge intro'),
        ('G361E', 'Path', 'G→E: +78.3 Å³\n+ charge intro'),
        ('G302A', 'Ben', 'G→A: +28.5 Å³\nminimal constraint'),
        ('G293W', 'Ben', 'G→W: +167.7 Å³\nbut near K292 PTM'),
    ]
    y_pos = np.arange(len(examples))
    colors_ex = ['#D94A4A' if e[1]=='Path' else '#4A90D9' for e in examples]
    bars = ax.barh(y_pos, [1]*len(examples), color=colors_ex, edgecolor='white', alpha=0.7)
    ax.set_yticks(y_pos)
    ax.set_yticklabels([e[0] for e in examples], fontsize=9, fontfamily='monospace')
    for i, e in enumerate(examples):
        ax.text(0.5, i, e[2], ha='center', va='center', fontsize=7)
    ax.set_xlim(0, 1)
    ax.set_xticks([])
    ax.set_title('D. Gate B: IDR Gly Constraint', fontweight='bold', fontsize=11)
    ax.invert_yaxis()
    # Legend
    p1 = mpatches.Patch(color='#D94A4A', alpha=0.7, label='Pathogenic')
    p2 = mpatches.Patch(color='#4A90D9', alpha=0.7, label='Benign')
    ax.legend(handles=[p1, p2], fontsize=8)

    plt.tight_layout()
    plt.savefig(f'{OUTDIR}/fig4_idr_discoveries.pdf')
    plt.savefig(f'{OUTDIR}/fig4_idr_discoveries.png')
    plt.close()
    print("Fig 4: done")

# ═══════════════════════════════════════════════════════════
# Fig 5: FN as missing physics map
# ═══════════════════════════════════════════════════════════
def fig5_missing_physics():
    fig, ax = plt.subplots(1, 1, figsize=(12, 7))

    categories = [
        ('Conservative\nmutations\n(D→E, L→V)', 19,
         'Partner complex\nstructures needed',
         'Binding geometry\nprecision'),
        ('PRD non-Pro\npositions\n(A→V, A→G)', 10,
         'PRD-SH3 complex\nstructure needed',
         'SH3 binding face\nidentity'),
        ('Linker orphans\n(no SLiM/PTM)', 10,
         'NMR / binding\ndata needed',
         'Functional\nannotation'),
        ('CTD 360-362\ncluster', 3,
         'Extended CT_reg\nor new motif',
         'Binding motif\nidentification'),
        ('Isolated IDR\nPro→X', 8,
         'Kuhn length\nmeasurement',
         'Polymer persistence\nlength'),
    ]

    x = np.arange(len(categories))
    bars = ax.bar(x, [c[1] for c in categories], color='#E8853D', edgecolor='white', width=0.6)

    ax.set_ylabel('Number of FN variants', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels([c[0] for c in categories], fontsize=9)
    ax.set_title('False Negatives = Missing Physics Map\n'
                 '"What data resolves each category?"',
                 fontweight='bold', fontsize=13)

    # Annotations: what data is needed (above bars)
    for i, c in enumerate(categories):
        ax.text(i, c[1] + 1.0, c[2], ha='center', va='bottom', fontsize=8,
                color='#2E5090', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#E8F0FE', edgecolor='#2E5090', alpha=0.8))

    # Below bars: physics needed
    for i, c in enumerate(categories):
        ax.text(i, -3.5, c[3], ha='center', va='top', fontsize=7,
                color='gray', style='italic')

    ax.set_ylim(-5, 28)
    ax.axhline(y=0, color='black', linewidth=0.5)

    # Summary text
    ax.text(0.98, 0.95, 'All 70 IDR FNs = missing Gates\nNOT threshold problems\n\n'
            'Principle 3: "If it\'s missed,\na Gate is missing"',
            transform=ax.transAxes, fontsize=9, va='top', ha='right',
            bbox=dict(boxstyle='round', facecolor='lightyellow', edgecolor='orange', alpha=0.9))

    plt.tight_layout()
    plt.savefig(f'{OUTDIR}/fig5_missing_physics.pdf')
    plt.savefig(f'{OUTDIR}/fig5_missing_physics.png')
    plt.close()
    print("Fig 5: done")

# ═══════════════════════════════════════════════════════════
# Fig 6: ClinVar vs molecular mechanism resolution
# ═══════════════════════════════════════════════════════════
def fig6_resolution():
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))

    # Panel A: FP reclassification
    ax = axes[0]
    labels = ['Definitive FP\n(Gate wrong)', 'Suspect FP\n(molecular TP,\nlow penetrance)']
    sizes = [13, 17]
    colors = ['#FFB3B3', '#FFE0B2']
    explode = (0, 0.05)
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct='%1.0f%%',
                                       startangle=90, explode=explode, textprops={'fontsize': 9})
    ax.set_title('A. IDR "False Positives" Reclassification\n(30 total)',
                 fontweight='bold', fontsize=11)

    # Panel B: Representative molecular TPs
    ax = axes[1]
    examples = [
        ('P47S', '[S/T]-P motif\nS46 phospho ↓', 'Biochem\nconfirmed'),
        ('R379S/L/H', 'NLS3 charge loss\nnuclear import ↓', 'Signal\npeptide'),
        ('K292R', 'Ubiquitin site\nε-NH₂ lost', 'Conjugation\nabolished'),
        ('S315T', 'Phosphosite\nkinase specificity', 'CDK1/2\nrecognition'),
        ('E388A/Q', 'CT_reg charge\npattern disrupted', 'Regulatory\ntail'),
        ('D393Y', 'S392 proximity\n+ charge loss', 'CK2/CDK2\nrecognition'),
    ]
    y = np.arange(len(examples))
    ax.barh(y, [1]*len(examples), color='#FFE0B2', edgecolor='#E8853D', height=0.7)
    for i, (var, mech, evidence) in enumerate(examples):
        ax.text(-0.02, i, var, ha='right', va='center', fontsize=9,
                fontfamily='monospace', fontweight='bold')
        ax.text(0.3, i, mech, ha='center', va='center', fontsize=8)
        ax.text(0.8, i, evidence, ha='center', va='center', fontsize=7,
                color='#2E5090', fontweight='bold')
    ax.set_xlim(-0.25, 1.0)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.invert_yaxis()
    ax.set_title('B. True Molecular Positives\n(ClinVar Benign, mechanism confirmed)',
                 fontweight='bold', fontsize=11)
    ax.text(0.5, -0.08, 'Gate & Channel resolution > ClinVar resolution',
            transform=ax.transAxes, ha='center', fontsize=10,
            color='#D94A4A', fontweight='bold', style='italic')

    plt.tight_layout()
    plt.savefig(f'{OUTDIR}/fig6_resolution.pdf')
    plt.savefig(f'{OUTDIR}/fig6_resolution.png')
    plt.close()
    print("Fig 6: done")

# ═══════════════════════════════════════════════════════════
# Run all
# ═══════════════════════════════════════════════════════════
if __name__ == '__main__':
    fig3_benchmark()
    fig4_idr_discoveries()
    fig5_missing_physics()
    fig6_resolution()
    print(f"\nAll figures saved to {OUTDIR}/")
    print("Files:")
    for f in sorted(os.listdir(OUTDIR)):
        print(f"  {f}")

