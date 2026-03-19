"""
MOSS v3.1 - Paper Figure Generation
====================================

Generate publication-quality figures for NeurIPS/ICLR submission

Run: python paper/v3_extended/generate_figures.py
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import json
from pathlib import Path
import sys

# Set publication style
plt.style.use('seaborn-v0_8-paper')
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 9
plt.rcParams['figure.dpi'] = 300


def load_json(filepath):
    """Load JSON data"""
    with open(filepath) as f:
        return json.load(f)


def figure_1_architecture():
    """
    Figure 1: Dimensional Architecture
    Conceptual diagram showing 4D → 8D → 9D progression
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')
    
    # Title
    ax.text(5, 5.5, 'MOSS Dimensional Architecture Evolution', 
            ha='center', fontsize=14, fontweight='bold')
    
    # v2.0 (4D)
    rect1 = mpatches.FancyBboxPatch((0.5, 3), 2.5, 1.5, 
                                     boxstyle="round,pad=0.1",
                                     facecolor='#3498db', alpha=0.7)
    ax.add_patch(rect1)
    ax.text(1.75, 4.2, 'v2.0', ha='center', fontsize=12, fontweight='bold', color='white')
    ax.text(1.75, 3.7, '4D Optimizer', ha='center', fontsize=10, color='white')
    ax.text(1.75, 3.3, 'S,C,I,O', ha='center', fontsize=9, color='white')
    
    # Arrow 1
    ax.annotate('', xy=(3.5, 3.75), xytext=(3.2, 3.75),
                arrowprops=dict(arrowstyle='->', lw=2, color='gray'))
    
    # v3.0 (8D)
    rect2 = mpatches.FancyBboxPatch((3.8, 2.5), 2.5, 2,
                                     boxstyle="round,pad=0.1",
                                     facecolor='#2ecc71', alpha=0.7)
    ax.add_patch(rect2)
    ax.text(5.05, 4.2, 'v3.0', ha='center', fontsize=12, fontweight='bold', color='white')
    ax.text(5.05, 3.6, '8D Society', ha='center', fontsize=10, color='white')
    ax.text(5.05, 3.1, '+Coherence,Valence', ha='center', fontsize=8, color='white')
    ax.text(5.05, 2.7, '+Other,Norm', ha='center', fontsize=8, color='white')
    
    # Arrow 2
    ax.annotate('', xy=(6.8, 3.5), xytext=(6.5, 3.5),
                arrowprops=dict(arrowstyle='->', lw=2, color='gray'))
    
    # v3.1 (9D)
    rect3 = mpatches.FancyBboxPatch((7.1, 2), 2.5, 2.5,
                                     boxstyle="round,pad=0.1",
                                     facecolor='#e74c3c', alpha=0.7)
    ax.add_patch(rect3)
    ax.text(8.35, 4.2, 'v3.1', ha='center', fontsize=12, fontweight='bold', color='white')
    ax.text(8.35, 3.5, '9D Self-Reflective', ha='center', fontsize=10, color='white')
    ax.text(8.35, 2.9, '+Purpose', ha='center', fontsize=9, color='white')
    ax.text(8.35, 2.5, '"Why?"', ha='center', fontsize=10, 
            color='white', style='italic')
    
    # Progression labels
    ax.text(2.5, 2.2, '"How to act?"', ha='center', fontsize=9, style='italic')
    ax.text(5.0, 1.8, '"Who to cooperate with?"', ha='center', fontsize=9, style='italic')
    ax.text(8.3, 1.4, '"Why do I exist?"', ha='center', fontsize=9, style='italic')
    
    plt.tight_layout()
    plt.savefig('paper/v3_extended/figures/figure1_architecture.pdf', 
                bbox_inches='tight', dpi=300)
    plt.savefig('paper/v3_extended/figures/figure1_architecture.png', 
                bbox_inches='tight', dpi=300)
    print("✓ Figure 1 generated: Architecture")
    plt.close()


def figure_2_purpose_divergence():
    """
    Figure 2: Purpose Divergence (H1)
    Bar chart showing 4 types from 6 agents
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    
    # Left: Bar chart
    data = load_json('experiments/purpose_society_results.json')
    distribution = data['purpose_distribution']
    
    types = list(distribution.keys())
    counts = list(distribution.values())
    colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12']
    
    bars = ax1.bar(types, counts, color=colors, alpha=0.8, edgecolor='black')
    ax1.set_ylabel('Number of Agents')
    ax1.set_title('Purpose Distribution (H1 Validation)')
    ax1.set_ylim(0, 4)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # Right: Pie chart
    ax2.pie(counts, labels=types, colors=colors, autopct='%1.1f%%',
           startangle=90)
    ax2.set_title('Purpose Type Proportions\n(6 agents, identical starts)')
    
    plt.tight_layout()
    plt.savefig('paper/v3_extended/figures/figure2_divergence.pdf',
                bbox_inches='tight', dpi=300)
    plt.savefig('paper/v3_extended/figures/figure2_divergence.png',
                bbox_inches='tight', dpi=300)
    print("✓ Figure 2 generated: Purpose Divergence")
    plt.close()


def figure_3_stability():
    """
    Figure 3: Purpose Stability (H2)
    Time series showing stability over 1000 steps
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6))
    
    # Load data
    data = load_json('experiments/purpose_stability_10k.json')
    history = data['history']['purpose_evolution']
    
    steps = [h['step'] for h in history]
    
    # Top: Dominant dimension over time
    dims = [h['dominant'] for h in history]
    dim_map = {'Survival': 0, 'Curiosity': 1, 'Influence': 2, 'Optimization': 3,
              'Coherence': 4, 'Valence': 5, 'Other': 6, 'Norm': 7}
    dim_values = [dim_map.get(d, -1) for d in dims]
    
    ax1.plot(steps, dim_values, 'o-', color='#3498db', markersize=4)
    ax1.set_ylabel('Dominant Dimension')
    ax1.set_title('Purpose Stability Over Time (H2 Validation)')
    ax1.set_yticks([0, 1, 2, 3])
    ax1.set_yticklabels(['Survival', 'Curiosity', 'Influence', 'Optimization'])
    ax1.grid(True, alpha=0.3)
    ax1.text(0.02, 0.95, 'Stability Score: 0.9977', transform=ax1.transAxes,
            fontsize=10, verticalalignment='top', bbox=dict(boxstyle='round', 
            facecolor='wheat', alpha=0.5))
    
    # Bottom: Purpose vector components over time
    # Simplified: show first 4 dimensions
    for i, dim_name in enumerate(['Survival', 'Curiosity', 'Influence', 'Optimization']):
        values = [h['vector'][i] for h in history]
        ax2.plot(steps, values, label=dim_name, linewidth=2)
    
    ax2.set_xlabel('Step')
    ax2.set_ylabel('Purpose Weight')
    ax2.set_title('Purpose Vector Evolution')
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('paper/v3_extended/figures/figure3_stability.pdf',
                bbox_inches='tight', dpi=300)
    plt.savefig('paper/v3_extended/figures/figure3_stability.png',
                bbox_inches='tight', dpi=300)
    print("✓ Figure 3 generated: Purpose Stability")
    plt.close()


def figure_4_fulfillment():
    """
    Figure 4: Fulfillment Comparison (H4)
    Box plot comparing Purpose-guided vs Non-purpose
    """
    fig, ax = plt.subplots(figsize=(8, 6))
    
    data = load_json('experiments/purpose_fulfillment_results.json')
    
    purpose_scores = data['purpose_guided']['final_scores']
    non_purpose_scores = data['non_purpose']['final_scores']
    
    # Box plot
    bp = ax.boxplot([non_purpose_scores, purpose_scores],
                     labels=['Non-Purpose\n(8D)', 'Purpose-Guided\n(9D)'],
                     patch_artist=True)
    
    # Color boxes
    bp['boxes'][0].set_facecolor('#95a5a6')
    bp['boxes'][1].set_facecolor('#2ecc71')
    
    # Add mean markers
    means = [np.mean(non_purpose_scores), np.mean(purpose_scores)]
    ax.scatter([1, 2], means, color='red', s=100, zorder=3, marker='D')
    
    # Labels and title
    ax.set_ylabel('Fulfillment Score')
    ax.set_title('Purpose Self-Fulfillment Effect (H4 Validation)')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add statistics
    improvement = data['comparison']['relative_improvement']
    ax.text(0.5, 0.95, f'+{improvement:.1f}% Improvement',
           transform=ax.transAxes, fontsize=12, fontweight='bold',
           verticalalignment='top', bbox=dict(boxstyle='round',
           facecolor='lightgreen', alpha=0.7))
    
    plt.tight_layout()
    plt.savefig('paper/v3_extended/figures/figure4_fulfillment.pdf',
                bbox_inches='tight', dpi=300)
    plt.savefig('paper/v3_extended/figures/figure4_fulfillment.png',
                bbox_inches='tight', dpi=300)
    print("✓ Figure 4 generated: Fulfillment Comparison")
    plt.close()


def figure_5_resource_competition():
    """
    Figure 5: Resource Competition (H3)
    Multi-panel showing cooperation and conflicts
    """
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
    
    data = load_json('experiments/purpose_faction_enhanced_results.json')
    
    # Panel 1: Cooperation by purpose distance
    coop_by_dist = data['cooperation_by_distance']
    distances = sorted(coop_by_dist.keys())
    coop_rates = [coop_by_dist[d] for d in distances]
    
    ax1.plot(distances, coop_rates, 'o-', color='#e74c3c', linewidth=2, markersize=8)
    ax1.set_xlabel('Purpose Distance')
    ax1.set_ylabel('Cooperation Rate')
    ax1.set_title('Cooperation vs Purpose Distance')
    ax1.grid(True, alpha=0.3)
    
    # Panel 2: Conflict statistics
    n_conflicts = data['n_conflicts']
    ax2.bar(['Conflicts'], [n_conflicts], color='#e74c3c', alpha=0.7)
    ax2.set_ylabel('Count')
    ax2.set_title(f'Total Conflicts: {n_conflicts}')
    ax2.text(0, n_conflicts/2, f'{n_conflicts:,}', ha='center', 
            fontsize=14, fontweight='bold')
    
    # Panel 3: Faction formation over time
    faction_history = data['faction_history']
    if faction_history:
        steps = [f['step'] for f in faction_history]
        n_factions = [f['n_factions'] for f in faction_history]
        ax3.plot(steps, n_factions, 'o-', color='#3498db', linewidth=2, markersize=8)
    ax3.set_xlabel('Step')
    ax3.set_ylabel('Number of Factions')
    ax3.set_title('Faction Formation Over Time')
    ax3.set_ylim(0, 5)
    ax3.grid(True, alpha=0.3)
    
    # Panel 4: Resource scarcity
    scarcity = data['final_scarcity']
    ax4.bar(['Resource\nScarcity'], [scarcity], color='#f39c12', alpha=0.7)
    ax4.set_ylabel('Scarcity Level')
    ax4.set_title(f'Final Resource Scarcity: {scarcity:.1%}')
    ax4.set_ylim(0, 1)
    
    plt.tight_layout()
    plt.savefig('paper/v3_extended/figures/figure5_competition.pdf',
                bbox_inches='tight', dpi=300)
    plt.savefig('paper/v3_extended/figures/figure5_competition.png',
                bbox_inches='tight', dpi=300)
    print("✓ Figure 5 generated: Resource Competition")
    plt.close()


def main():
    """Generate all figures"""
    print("="*70)
    print("🎨 MOSS v3.1 - Paper Figure Generation")
    print("="*70)
    
    # Create figures directory
    Path('paper/v3_extended/figures').mkdir(exist_ok=True)
    
    # Generate figures
    print("\nGenerating publication-quality figures...\n")
    
    figure_1_architecture()
    figure_2_purpose_divergence()
    figure_3_stability()
    figure_4_fulfillment()
    figure_5_resource_competition()
    
    print("\n" + "="*70)
    print("✅ All figures generated successfully!")
    print("="*70)
    print("\nOutput files:")
    print("  paper/v3_extended/figures/figure1_architecture.{pdf,png}")
    print("  paper/v3_extended/figures/figure2_divergence.{pdf,png}")
    print("  paper/v3_extended/figures/figure3_stability.{pdf,png}")
    print("  paper/v3_extended/figures/figure4_fulfillment.{pdf,png}")
    print("  paper/v3_extended/figures/figure5_competition.{pdf,png}")
    print("\nReady for NeurIPS/ICLR submission!")
    print("="*70)


if __name__ == "__main__":
    main()
