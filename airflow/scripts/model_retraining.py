# airflow/scripts/model_retraining.py
"""
Model retraining script for OffScript retraining pipeline.

Uses a sliding window approach — trains only on the most recent
N months of data rather than combining all historical data with
fresh data. This avoids the distribution mixing problem where
the model must reconcile two different eras simultaneously.

The window size is configurable. A 12-month window keeps one
full season of data ensuring sufficient sample size while
staying current with evolving pitcher behavior patterns.

Called by the Airflow DAG as Task 3 of 5.
"""

import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import accuracy_score, balanced_accuracy_score
import xgboost as xgb

# ── Configuration ─────────────────────────────────────────────────────────

BASELINE_PATH  = Path('/opt/airflow/data/processed/pitcher_data_clean.parquet')
FRESH_PATH     = Path('/opt/airflow/data/fresh/pitcher_data_fresh.parquet')
NEW_MODEL_DIR  = Path('/opt/airflow/models/candidate')
NEW_MODEL_PATH = NEW_MODEL_DIR / 'baseline_pitch_model.pkl'
NEW_LE_PATH    = NEW_MODEL_DIR / 'label_encoder.pkl'
NEW_PE_PATH    = NEW_MODEL_DIR / 'pitcher_encoder.pkl'

FEATURE_COLS = [
    'balls', 'strikes', 'inning', 'score_diff',
    'on_1b', 'on_2b', 'on_3b',
    'runners_on', 'scoring_position',
    'stand_encoded', 'pitcher_encoded', 'count_leverage'
]

# Sliding window size in months.
# 12 = train on most recent 12 months of data only.
# Increase if sample size is too small after windowing.
WINDOW_MONTHS = 12


def engineer_features(df: pd.DataFrame,
                      pitcher_encoder: LabelEncoder) -> pd.DataFrame:
    """Apply feature engineering matching the original training pipeline."""
    df = df.copy()

    df['stand_encoded'] = (df['stand'] == 'R').astype(int)
    df['runners_on'] = (
        df['on_1b'].fillna(0) +
        df['on_2b'].fillna(0) +
        df['on_3b'].fillna(0)
    )
    df['scoring_position'] = (
        (df['on_2b'].fillna(0) + df['on_3b'].fillna(0)) > 0
    ).astype(int)
    df['count_leverage'] = (
        (df['strikes'] == 2).astype(int) * 2 +
        (df['balls'] == 3).astype(int) * 2 +
        (df['strikes'] == 1).astype(int) +
        (df['balls'] == 2).astype(int)
    )

    known_pitchers = set(pitcher_encoder.classes_)
    df = df[df['pitcher_name'].isin(known_pitchers)].copy()
    df['pitcher_encoded'] = pitcher_encoder.transform(df['pitcher_name'])

    return df


def apply_sliding_window(df: pd.DataFrame,
                          window_months: int) -> pd.DataFrame:
    """
    Filter dataset to only include pitches within the sliding window.

    Args:
        df: Combined DataFrame with game_date column
        window_months: Number of months to include from most recent date

    Returns:
        Filtered DataFrame containing only window period data
    """
    df = df.copy()
    df['game_date'] = pd.to_datetime(df['game_date'])

    # Calculate window cutoff from most recent pitch in dataset
    most_recent = df['game_date'].max()
    cutoff_date = most_recent - pd.DateOffset(months=window_months)

    windowed = df[df['game_date'] >= cutoff_date].copy()

    print(f"  Most recent pitch:  {most_recent.date()}")
    print(f"  Window cutoff:      {cutoff_date.date()}")
    print(f"  Pitches in window:  {len(windowed):,}")
    print(f"  Pitches excluded:   {len(df) - len(windowed):,}")

    return windowed


def run():
    """Main entry point — applies sliding window, retrains, saves candidate."""
    print("=" * 60)
    print("OffScript Model Retraining — Phase 11B")
    print(f"Sliding window approach — {WINDOW_MONTHS} month window")
    print("=" * 60)

    NEW_MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # Load and combine datasets
    baseline = pd.read_parquet(BASELINE_PATH)
    fresh    = pd.read_parquet(FRESH_PATH)

    print(f"Baseline pitches: {len(baseline):,}")
    print(f"Fresh pitches:    {len(fresh):,}")

    combined = pd.concat([baseline, fresh], ignore_index=True)
    combined = combined.dropna(subset=['pitch_type'])
    print(f"Combined pitches: {len(combined):,}")

    # Apply sliding window — keep only most recent N months
    print(f"\nApplying {WINDOW_MONTHS}-month sliding window...")
    windowed = apply_sliding_window(combined, WINDOW_MONTHS)

    if len(windowed) < 5000:
        print(f"WARNING: Window contains only {len(windowed):,} pitches.")
        print(f"Consider increasing WINDOW_MONTHS for adequate sample size.")

    # Build pitcher encoder from windowed data
    # Only encode pitchers present in the window
    pitcher_encoder = LabelEncoder()
    pitcher_encoder.fit(windowed['pitcher_name'].unique())
    print(f"\nPitchers in window: {len(pitcher_encoder.classes_)}")

    # Engineer features
    windowed_engineered = engineer_features(windowed, pitcher_encoder)
    print(f"Pitches after feature engineering: {len(windowed_engineered):,}")

    # Prepare feature matrix and target
    X = windowed_engineered[FEATURE_COLS].fillna(0)
    le = LabelEncoder()
    y = le.fit_transform(windowed_engineered['pitch_type'])

    print(f"Pitch types in window: {le.classes_.tolist()}")

    # Stratified train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        stratify=y,
        random_state=42
    )

    print(f"\nTraining samples: {len(X_train):,}")
    print(f"Testing samples:  {len(X_test):,}")

    # Class weights for pitch type imbalance
    classes = np.unique(y_train)
    class_weights = compute_class_weight(
        class_weight='balanced',
        classes=classes,
        y=y_train
    )
    class_weights = np.clip(class_weights, 0.5, 2.0)
    sample_weights = class_weights[y_train]

    # Train model on windowed data only
    print("\nTraining XGBoost classifier on windowed data...")
    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric='mlogloss',
        random_state=42
    )
    model.fit(X_train, y_train, sample_weight=sample_weights)

    # Evaluate on test set
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    balanced = balanced_accuracy_score(y_test, y_pred)

    print(f"\nCandidate Model Performance:")
    print(f"  Accuracy:          {accuracy:.3f}")
    print(f"  Balanced Accuracy: {balanced:.3f}")
    print(f"  Window: {WINDOW_MONTHS} months of most recent data")

    # Save candidate model and encoders
    joblib.dump(model, NEW_MODEL_PATH)
    joblib.dump(le, NEW_LE_PATH)
    joblib.dump(pitcher_encoder, NEW_PE_PATH)

    print(f"\nCandidate model saved to {NEW_MODEL_DIR}")

    return {
        'accuracy': float(accuracy),
        'balanced_accuracy': float(balanced),
        'training_samples': int(len(X_train)),
        'test_samples': int(len(X_test)),
        'pitch_types': le.classes_.tolist(),
        'window_months': WINDOW_MONTHS,
        'window_pitches': int(len(windowed)),
        'weighting': 'class_balanced_sliding_window'
    }


if __name__ == '__main__':
    run()