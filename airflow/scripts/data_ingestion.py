# airflow/scripts/data_ingestion.py
"""
Data ingestion script for OffScript retraining pipeline.

Pulls fresh Statcast pitch-by-pitch data for the current season
for all 14 pitchers in the OffScript roster. Saves the new data
as a parquet file for use in downstream pipeline tasks.

Called by the Airflow DAG as Task 1 of 5.
"""

import os
import pandas as pd
from pathlib import Path
from datetime import datetime
from pybaseball import statcast_pitcher, cache

cache.enable()

# ── Configuration ─────────────────────────────────────────────────────────

# All 14 pitchers with their MLBAM IDs
PITCHERS = {
    'Chris Sale':       519242,
    'Corbin Burnes':    669203,
    'Dylan Cease':      656302,
    'Framber Valdez':   664285,
    'Gerrit Cole':      543037,
    'Justin Verlander': 434378,
    'Kyle Hendricks':   543294,
    'Logan Webb':       657277,
    'Marcus Stroman':   543135,
    'Max Scherzer':     453286,
    'Nestor Cortes':    641482,
    'Spencer Strider':  675911,
    'Yusei Kikuchi':    579328,
    'Zack Wheeler':     554430,
}

# Columns needed for retraining — matches original training set
COLS_OF_INTEREST = [
    'game_date', 'pitcher', 'player_name',
    'pitch_type', 'pitch_name',
    'release_speed', 'pfx_x', 'pfx_z',
    'plate_x', 'plate_z',
    'balls', 'strikes',
    'on_1b', 'on_2b', 'on_3b',
    'stand', 'p_throws',
    'events', 'description',
    'inning', 'home_score', 'away_score',
    'batter', 'bat_score', 'fld_score',
]

# Fresh data covers 2025 season
FRESH_START_DATE = '2025-03-27'
FRESH_END_DATE   = '2025-11-01'

# Output path inside container — mapped to local data/ via volume
OUTPUT_DIR  = Path('/opt/airflow/data/fresh')
OUTPUT_PATH = OUTPUT_DIR / 'pitcher_data_fresh.parquet'


def fix_baserunner_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Convert baserunner columns from player IDs to binary flags."""
    for col in ['on_1b', 'on_2b', 'on_3b']:
        if col in df.columns:
            df[col] = (df[col].fillna(0) != 0).astype(int)
    return df


def pull_pitcher_data(name: str, pid: int) -> pd.DataFrame | None:
    """Pull Statcast data for a single pitcher and return cleaned DataFrame."""
    print(f"  Pulling {name}...")
    try:
        df = statcast_pitcher(FRESH_START_DATE, FRESH_END_DATE, pid)
        if df is None or len(df) == 0:
            print(f"  WARNING: No data returned for {name}")
            return None

        # Keep only required columns that exist in the response
        available = [c for c in COLS_OF_INTEREST if c in df.columns]
        df = df[available].copy()
        df['pitcher_name'] = name

        # Engineer derived columns
        df['count'] = (
            df['balls'].astype(str) + '-' + df['strikes'].astype(str)
        )
        df['score_diff'] = df['home_score'] - df['away_score']
        df = fix_baserunner_columns(df)

        print(f"  {name}: {len(df):,} pitches")
        return df

    except Exception as e:
        print(f"  ERROR pulling {name}: {e}")
        return None


def run():
    """Main entry point — pulls all pitchers and saves combined dataset."""
    print("=" * 60)
    print("OffScript Data Ingestion")
    print(f"Season range: {FRESH_START_DATE} to {FRESH_END_DATE}")
    print(f"Pitchers: {len(PITCHERS)}")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_data = []
    for name, pid in PITCHERS.items():
        df = pull_pitcher_data(name, pid)
        if df is not None:
            all_data.append(df)

    if not all_data:
        raise RuntimeError(
            "No data pulled for any pitcher. "
            "Check date range and internet connectivity."
        )

    combined = pd.concat(all_data, ignore_index=True)

    # Remove rows with missing pitch type — cannot train without target
    before = len(combined)
    combined = combined.dropna(subset=['pitch_type'])
    after = len(combined)
    print(f"\nRows removed (missing pitch_type): {before - after:,}")

    combined.to_parquet(OUTPUT_PATH, index=False)

    print(f"\nFresh data saved to {OUTPUT_PATH}")
    print(f"Total pitches: {len(combined):,}")
    print(f"Pitchers: {combined['pitcher_name'].nunique()}")
    print(f"Date range: {combined['game_date'].min()} "
          f"to {combined['game_date'].max()}")
    print(f"Pitch types: {sorted(combined['pitch_type'].unique())}")

    return str(OUTPUT_PATH)


if __name__ == '__main__':
    run()