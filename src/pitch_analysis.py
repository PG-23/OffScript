# src/pitch_analysis.py

import pandas as pd
import matplotlib.pyplot as plt

def pitch_usage_by_count(data, pitcher_name):
    """Calculate pitch type usage percentage by count state."""
    count_pitch = (
        data.groupby(['count', 'pitch_type'])
        .size()
        .reset_index(name='n')
    )
    count_pitch['pct'] = (count_pitch.groupby('count')['n']
                          .transform(lambda x: x / x.sum() * 100))
    return count_pitch

def compare_pitch_usage(data1, name1, data2, name2):
    """Compare pitch usage between two pitchers side by side."""
    fig, axes = plt.subplots(1, 2, figsize=(20, 6))
    
    for ax, data, name in zip(axes, [data1, data2], [name1, name2]):
        cp = pitch_usage_by_count(data, name)
        pivot = (cp.pivot(index='count', columns='pitch_type', values='pct')
                 .fillna(0))
        pivot.plot(kind='bar', stacked=True, ax=ax, colormap='tab10')
        ax.set_title(f"{name} — Pitch Selection by Count")
        ax.set_ylabel("Usage %")
        ax.set_xlabel("Count")
        ax.legend(title="Pitch Type", bbox_to_anchor=(1.05, 1))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    plt.savefig('../reports/figures/pitcher_comparison.png',
                dpi=150, bbox_inches='tight')
    plt.show()