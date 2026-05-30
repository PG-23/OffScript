# airflow/scripts/model_retraining.py
"""
Model retraining script for OffScript retraining pipeline.

Combines the original 2023-2024 training data with fresh 2025 data,
retrains the XGBoost pitch selection classifier, and saves the new
model and encoders for evaluation.

Called by the Airflow DAG as Task 3 of 5.
"""

import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
import xgboost as xgb

# ── Configuration ─────────────────────────────────────────────────────────

BASELINE_PATH   = Path('/opt/airflow/data/processed/pitcher_data_clean.parquet')
FRESH_PATH      = Path('/opt/airflow/data/fresh/pitcher_data_fresh.parquet')
NEW_MODEL_DIR   = Path('/opt/airflow/models/candidate')
NEW_MODEL_PATH  = NEW_MODEL_DIR / 'baseline_pitch_model.pkl'
NEW_LE_PATH     = NEW_MODEL_DIR / 'label_encoder.pkl'
NEW_PE_PATH     = NEW_MODEL_DIR / 'pitcher_encoder.pkl'

FEATURE_COLS = [
    'balls', 'strikes', 'inning', 'score_diff',
    'on_1b', 'on_2b', 'on_3b',
    'runners_on', 'scoring_position',
    'stand_encoded', 'pitcher_encoded', 'count_leverage'
]


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

    # Encode pitcher — handle unseen pitchers gracefully
    known_pitchers = set(pitcher_encoder.classes_)
    df = df[df['pitcher_name'].isin(known_pitchers)].copy()
    df['pitcher_encoded'] = pitcher_encoder.transform(df['pitcher_name'])

    return df


def run():
    """Main entry point — combines data, retrains model, saves candidate."""
    print("=" * 60)
    print("OffScript Model Retraining")
    print("=" * 60)

    NEW_MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # Load datasets
    baseline = pd.read_parquet(BASELINE_PATH)
    fresh    = pd.read_parquet(FRESH_PATH)

    print(f"Baseline pitches: {len(baseline):,}")
    print(f"Fresh pitches:    {len(fresh):,}")

    # Combine datasets
    combined = pd.concat([baseline, fresh], ignore_index=True)
    combined = combined.dropna(subset=['pitch_type'])
    print(f"Combined pitches: {len(combined):,}")

    # Build pitcher encoder from combined data
    pitcher_encoder = LabelEncoder()
    pitcher_encoder.fit(combined['pitcher_name'].unique())

    # Engineer features
    combined = engineer_features(combined, pitcher_encoder)

    # Prepare feature matrix and target
    X = combined[FEATURE_COLS].fillna(0)
    le = LabelEncoder()
    y = le.fit_transform(combined['pitch_type'])

    # Stratified train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        stratify=y,
        random_state=42
    )

    print(f"\nTraining samples: {len(X_train):,}")
    print(f"Testing samples:  {len(X_test):,}")

    # Class weights
    classes = np.unique(y_train)
    class_weights = compute_class_weight(
        class_weight='balanced',
        classes=classes,
        y=y_train
    )
    class_weights = np.clip(class_weights, 0.5, 2.0)
    sample_weights = class_weights[y_train]

    # Train model
    print("\nTraining XGBoost classifier...")
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

    # Quick evaluation
    from sklearn.metrics import accuracy_score, balanced_accuracy_score
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    balanced = balanced_accuracy_score(y_test, y_pred)

    print(f"\nCandidate Model Performance:")
    print(f"  Accuracy:          {accuracy:.3f}")
    print(f"  Balanced Accuracy: {balanced:.3f}")

    # Save candidate model and encoders
    joblib.dump(model, NEW_MODEL_PATH)
    joblib.dump(le, NEW_LE_PATH)
    joblib.dump(pitcher_encoder, NEW_PE_PATH)

    print(f"\nCandidate model saved to {NEW_MODEL_DIR}")

    return {
        'accuracy': accuracy,
        'balanced_accuracy': balanced,
        'training_samples': len(X_train),
        'test_samples': len(X_test),
        'pitch_types': le.classes_.tolist()
    }


if __name__ == '__main__':
    run()