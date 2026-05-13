# src/pitch_analysis.py
"""Shared utility functions for pitch analysis, visualization, and data loading.

This module is imported by all analysis notebooks and provides a consistent
interface for loading Statcast data, computing pitch usage breakdowns, and
generating standard visualizations.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data(path: str = "../data/processed/pitcher_data.parquet") -> pd.DataFrame:
    """Load the combined pitcher dataset.

    Args:
        path: Path to the raw combined parquet file.

    Returns:
        DataFrame containing all pitcher pitch-level records.
    """
    return pd.read_parquet(path)


def load_clean_data(path: str = "../data/processed/pitcher_data_clean.parquet") -> pd.DataFrame:
    """Load the cleaned pitcher dataset prepared for modeling.

    Statcast encodes baserunner columns as MLBAM player IDs rather than binary
    flags. This function converts those columns to 1/0 indicators so downstream
    models can treat them as boolean features.

    Args:
        path: Path to the cleaned parquet file.

    Returns:
        DataFrame with baserunner columns encoded as binary integers (0 or 1).
    """
    data = pd.read_parquet(path)

    for col in ("on_1b", "on_2b", "on_3b"):
        if col in data.columns:
            data[col] = (data[col].fillna(0) != 0).astype(int)

    return data


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

def get_pitcher(data: pd.DataFrame, name: str) -> pd.DataFrame:
    """Return all pitch-level records for a single pitcher.

    Args:
        data: Full pitcher dataset as returned by load_data or load_clean_data.
        name: Pitcher's full name exactly as it appears in the pitcher_name column.

    Returns:
        A filtered copy of data containing only rows for the specified pitcher.
    """
    return data[data["pitcher_name"] == name].copy()


# ---------------------------------------------------------------------------
# Usage calculations
# ---------------------------------------------------------------------------

def pitch_usage_by_count(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate pitch type usage percentage broken down by count state.

    Args:
        data: Pitch-level DataFrame for a single pitcher or the full dataset.

    Returns:
        DataFrame with columns: count, pitch_type, n (raw count), pct (usage %).
    """
    count_pitch = (
        data.groupby(["count", "pitch_type"])
        .size()
        .reset_index(name="n")
    )
    count_pitch["pct"] = count_pitch.groupby("count")["n"].transform(
        lambda x: x / x.sum() * 100
    )
    return count_pitch


def pitch_usage_by_handedness(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate pitch type usage percentage split by batter handedness.

    Args:
        data: Pitch-level DataFrame for a single pitcher or the full dataset.

    Returns:
        DataFrame with columns: stand (L/R), pitch_type, n (raw count), pct (usage %).
    """
    hand_pitch = (
        data.groupby(["stand", "pitch_type"])
        .size()
        .reset_index(name="n")
    )
    hand_pitch["pct"] = hand_pitch.groupby("stand")["n"].transform(
        lambda x: x / x.sum() * 100
    )
    return hand_pitch


# ---------------------------------------------------------------------------
# Visualization helpers
# ---------------------------------------------------------------------------

def plot_strike_zone(ax: plt.Axes) -> None:
    """Draw a regulation strike zone outline on an existing matplotlib axis.

    The zone is drawn as a black rectangle using standard MLB dimensions
    (17 inches wide, approximately 1.5 to 3.5 feet in height).

    Args:
        ax: The matplotlib Axes object to draw the strike zone on.
    """
    zone = patches.Rectangle(
        (-0.85, 1.5), 1.7, 2.0,
        linewidth=2,
        edgecolor="black",
        facecolor="none",
    )
    ax.add_patch(zone)
    ax.set_xlim(-2.5, 2.5)
    ax.set_ylim(0, 5)


def plot_pitch_locations(
    data: pd.DataFrame,
    pitcher_name: str,
    save: bool = True,
) -> None:
    """Plot pitch location scatter plots by pitch type for a single pitcher.

    Generates one subplot per pitch type, each showing a strike zone overlay
    with individual pitch locations as a scatter plot.

    Args:
        data: Pitch-level DataFrame filtered to a single pitcher.
        pitcher_name: Pitcher's full name, used for the figure title and
            the output filename when save is True.
        save: If True, saves the figure to reports/figures/ as a PNG.
            Defaults to True.
    """
    pitches = data["pitch_type"].dropna().unique()
    n = len(pitches)
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 6))
    if n == 1:
        axes = [axes]

    for ax, pitch in zip(axes, pitches):
        subset = data[data["pitch_type"] == pitch]
        plot_strike_zone(ax)
        ax.scatter(
            subset["plate_x"],
            subset["plate_z"],
            alpha=0.15,
            s=10,
            color="steelblue",
        )
        ax.set_title(f"{pitch}\nn={len(subset)}")
        ax.set_xlabel("Horizontal")
        ax.set_ylabel("Vertical")

    fig.suptitle(f"{pitcher_name} — Pitch Locations by Type", fontsize=14, y=1.02)
    plt.tight_layout()

    if save:
        safe_name = pitcher_name.lower().replace(" ", "_")
        plt.savefig(
            f"../reports/figures/{safe_name}_locations.png",
            dpi=150,
            bbox_inches="tight",
        )
    plt.show()


def plot_usage_comparison(
    data: pd.DataFrame,
    name1: str,
    name2: str,
    save: bool = True,
) -> None:
    """Plot a side-by-side stacked bar comparison of pitch selection by count.

    Generates a two-panel figure showing how each pitcher distributes their
    pitch types across all count states, useful for identifying strategic
    differences between pitchers.

    Args:
        data: Full pitcher dataset containing records for both pitchers.
        name1: Full name of the first pitcher.
        name2: Full name of the second pitcher.
        save: If True, saves the figure to reports/figures/pitcher_comparison.png.
            Defaults to True.
    """
    fig, axes = plt.subplots(1, 2, figsize=(20, 6))

    for ax, name in zip(axes, [name1, name2]):
        pitcher_data = get_pitcher(data, name)
        cp = pitch_usage_by_count(pitcher_data)
        pivot = cp.pivot(index="count", columns="pitch_type", values="pct").fillna(0)
        pivot.plot(kind="bar", stacked=True, ax=ax, colormap="tab10")
        ax.set_title(f"{name} — Pitch Selection by Count")
        ax.set_ylabel("Usage %")
        ax.set_xlabel("Count")
        ax.legend(title="Pitch Type", bbox_to_anchor=(1.05, 1))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

    plt.tight_layout()
    if save:
        plt.savefig(
            "../reports/figures/pitcher_comparison.png",
            dpi=150,
            bbox_inches="tight",
        )
    plt.show()