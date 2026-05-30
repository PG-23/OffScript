# airflow/scripts/model_evaluation.py
"""
Model evaluation script for OffScript retraining pipeline.

Compares the candidate retrained model against the currently
deployed model on a held-out test set. Only recommends deployment
if the new model achieves equal or better balanced accuracy.

Called by the Airflow DAG as Task 4 of 5.
"""

import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import accuracy_score, balanced_accuracy_score
from sklearn.model_selection import train_test_split

# ── Configuration ─────────────────────────────────────────────────────────

BASELINE_PATH      = Path('/opt/airflow/data/processed/pitcher_data_clean.parquet')
FRESH_PATH         = Path('/opt/airflow/data/fresh/pitcher_data_fresh.parquet')
CURRENT_MODEL_PATH = Path('/opt/airflow/models/baseline_pitch_model.pkl')
CURRENT_LE_PATH    = Path('/opt/airflow/models/label_encoder.pkl')
CURRENT_PE_PATH    = Path('/opt/airflow/models/pitcher_encoder.pkl')
CANDIDATE_DIR      = Path('/opt/airflow/models/candidate')
EVAL_REPORT_PATH   = Path('/opt/airflow/data/fresh/evaluation_report.json')

FEATURE_COLS = [
    'balls', 'strikes', 'inning', 'score_diff',
    'on_1b', 'on_2b', 'on_3b',
    'runners_on', 'scoring_position',
    'stand_encoded', 'pitcher_encoded', 'count_leverage'
]


def engineer_features(df: pd.DataFrame,
                       pitcher_encoder) -> pd.DataFrame:
    """Apply feature engineering for model evaluation."""
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
    known = set(pitcher_encoder.classes_)
    df = df[df['pitcher_name'].isin(known)].copy()
    df['pitcher_encoded'] = pitcher_encoder.transform(df['pitcher_name'])
    return df


def evaluate_model(model, le, pe, df: pd.DataFrame) -> dict:
    """Evaluate a model on the provided dataset."""
    df = engineer_features(df, pe)
    df = df.dropna(subset=['pitch_type'])

    # Filter to pitch types the encoder knows
    known_pitches = set(le.classes_)
    df = df[df['pitch_type'].isin(known_pitches)].copy()

    X = df[FEATURE_COLS].fillna(0)
    y = le.transform(df['pitch_type'])

    y_pred = model.predict(X)
    return {
        'accuracy': float(accuracy_score(y, y_pred)),
        'balanced_accuracy': float(balanced_accuracy_score(y, y_pred)),
        'samples_evaluated': len(y)
    }


def run():
    """Main entry point — evaluates both models and decides on deployment."""
    print("=" * 60)
    print("OffScript Model Evaluation")
    print("=" * 60)

    EVAL_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Load fresh data as evaluation set
    fresh = pd.read_parquet(FRESH_PATH)
    print(f"Evaluation dataset: {len(fresh):,} pitches")

    # Load current production model
    print("\nLoading current production model...")
    current_model = joblib.load(CURRENT_MODEL_PATH)
    current_le    = joblib.load(CURRENT_LE_PATH)
    current_pe    = joblib.load(CURRENT_PE_PATH)

    # Load candidate model
    print("Loading candidate model...")
    candidate_model = joblib.load(CANDIDATE_DIR / 'baseline_pitch_model.pkl')
    candidate_le    = joblib.load(CANDIDATE_DIR / 'label_encoder.pkl')
    candidate_pe    = joblib.load(CANDIDATE_DIR / 'pitcher_encoder.pkl')

    # Evaluate both models on fresh data
    print("\nEvaluating current model on fresh data...")
    current_metrics = evaluate_model(
        current_model, current_le, current_pe, fresh
    )

    print("Evaluating candidate model on fresh data...")
    candidate_metrics = evaluate_model(
        candidate_model, candidate_le, candidate_pe, fresh
    )

    # Deployment decision
    improvement = (
        candidate_metrics['balanced_accuracy'] -
        current_metrics['balanced_accuracy']
    )
    deploy_candidate = improvement >= 0

    print(f"\n=== Evaluation Results ===")
    print(f"Current model balanced accuracy:   "
          f"{current_metrics['balanced_accuracy']:.3f}")
    print(f"Candidate model balanced accuracy: "
          f"{candidate_metrics['balanced_accuracy']:.3f}")
    print(f"Improvement:                       {improvement:+.3f}")
    print(f"Deploy candidate:                  {deploy_candidate}")

    report = {
        'deploy_candidate': deploy_candidate,
        'improvement': improvement,
        'current_model': current_metrics,
        'candidate_model': candidate_metrics
    }

    EVAL_REPORT_PATH.write_text(json.dumps(report, indent=2))
    print(f"\nEvaluation report saved to {EVAL_REPORT_PATH}")

    return report


if __name__ == '__main__':
    run()