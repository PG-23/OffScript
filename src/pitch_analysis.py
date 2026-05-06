# src/pitch_analysis.py

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import seaborn as sns

def load_data(path='../data/processed/pitcher_data.parquet'):
    """Load the combined pitcher dataset."""
    return pd.read_parquet(path)

def get_pitcher(data, name):
    """Filter dataset to a single pitcher."""
    return data[data['pitcher_name'] == name].copy()

def pitch_usage_by_count(data):
    """Calculate pitch type usage percentage by count state."""
    count_pitch = (
        data.groupby(['count', 'pitch_type'])
        .size()
        .reset_index(name='n')
    )
    count_pitch['pct'] = (
        count_pitch.groupby('count')['n']
        .transform(lambda x: x / x.sum() * 100)
    )
    return count_pitch

def pitch_usage_by_handedness(data):
    """Calculate pitch usage split by batter handedness."""
    hand_pitch = (
        data.groupby(['stand', 'pitch_type'])
        .size()
        .reset_index(name='n')
    )
    hand_pitch['pct'] = (
        hand_pitch.groupby('stand')['n']
        .transform(lambda x: x / x.sum() * 100)
    )
    return hand_pitch

def plot_strike_zone(ax):
    """Draw a standard strike zone on a matplotlib axis."""
    zone = patches.Rectangle(
        (-0.85, 1.5), 1.7, 2.0,
        linewidth=2, edgecolor='black', facecolor='none'
    )
    ax.add_patch(zone)
    ax.set_xlim(-2.5, 2.5)
    ax.set_ylim(0, 5)

def plot_pitch_locations(data, pitcher_name, save=True):
    """Plot pitch location heat map by pitch type."""
    pitches = data['pitch_type'].dropna().unique()
    n = len(pitches)
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 6))
    if n == 1:
        axes = [axes]

    for ax, pitch in zip(axes, pitches):
        subset = data[data['pitch_type'] == pitch]
        plot_strike_zone(ax)
        ax.scatter(subset['plate_x'], subset['plate_z'],
                  alpha=0.15, s=10, color='steelblue')
        ax.set_title(f"{pitch}\nn={len(subset)}")
        ax.set_xlabel("Horizontal")
        ax.set_ylabel("Vertical")

    fig.suptitle(f"{pitcher_name} — Pitch Locations by Type", 
                 fontsize=14, y=1.02)
    plt.tight_layout()

    if save:
        safe_name = pitcher_name.lower().replace(' ', '_')
        plt.savefig(
            f'../reports/figures/{safe_name}_locations.png',
            dpi=150, bbox_inches='tight'
        )
    plt.show()

def plot_usage_comparison(data, name1, name2, save=True):
    """Compare pitch selection by count between two pitchers."""
    fig, axes = plt.subplots(1, 2, figsize=(20, 6))

    for ax, name in zip(axes, [name1, name2]):
        pitcher_data = get_pitcher(data, name)
        cp = pitch_usage_by_count(pitcher_data)
        pivot = (cp.pivot(index='count', columns='pitch_type', values='pct')
                 .fillna(0))
        pivot.plot(kind='bar', stacked=True, ax=ax, colormap='tab10')
        ax.set_title(f"{name} — Pitch Selection by Count")
        ax.set_ylabel("Usage %")
        ax.set_xlabel("Count")
        ax.legend(title="Pitch Type", bbox_to_anchor=(1.05, 1))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

    plt.tight_layout()
    if save:
        plt.savefig('../reports/figures/pitcher_comparison.png',
                    dpi=150, bbox_inches='tight')
    plt.show()