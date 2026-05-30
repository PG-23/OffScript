# airflow/scripts/drift_detection.py
"""
Drift detection script for OffScript retraining pipeline.

Compares the pitch type distribution in fresh 2025 data against
the 2023-2024 training baseline using statistical tests. Flags
significant drift that may indicate pitcher behavior changes or
model staleness.

Called by the Airflow DAG as Task 2 of 5.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

# ── Configuration ─────────────────────────────────────────────────────────

BASELINE_PATH = Path('/opt/airflow/data/processed/pitcher_data_clean.parquet')
FRESH_PATH    = Path('/opt/airflow/data/fresh/pitcher_data_fresh.parquet')
REPORT_PATH   = Path('/opt/airflow/data/fresh/drift_report.json')

# Threshold for flagging drift — p-value below this triggers retraining
DRIFT_THRESHOLD = 0.05

# Minimum fresh pitches required to run drift detection
MIN_FRESH_PITCHES = 1000


def get_pitch_distribution(df: pd.DataFrame) -> pd.Series:
    """Return normalized pitch type distribution."""
    return df['pitch_type'].value_counts(normalize=True).sort_index()


def calculate_psi(baseline: pd.Series, fresh: pd.Series) -> float:
    """
    Calculate Population Stability Index (PSI).
    PSI < 0.1  — no significant drift
    PSI < 0.2  — moderate drift, monitor closely
    PSI >= 0.2 — significant drift, retraining recommended
    """
    # Align indices so both series have the same pitch types
    all_pitches = baseline.index.union(fresh.index)
    baseline = baseline.reindex(all_pitches, fill_value=0.001)
    fresh    = fresh.reindex(all_pitches, fill_value=0.001)

    psi = np.sum(
        (fresh - baseline) * np.log(fresh / baseline)
    )
    return float(psi)


def run():
    """Main entry point — compares distributions and writes drift report."""
    print("=" * 60)
    print("OffScript Drift Detection")
    print("=" * 60)

    # Load datasets
    baseline = pd.read_parquet(BASELINE_PATH)
    fresh    = pd.read_parquet(FRESH_PATH)

    print(f"Baseline pitches: {len(baseline):,}")
    print(f"Fresh pitches:    {len(fresh):,}")

    if len(fresh) < MIN_FRESH_PITCHES:
        print(f"WARNING: Insufficient fresh data ({len(fresh)} pitches). "
              f"Minimum required: {MIN_FRESH_PITCHES}")
        report = {
            'drift_detected': bool(drift_detected),
            'retraining_recommended': bool(retraining_recommended),
            'chi2_statistic': float(chi2),
            'p_value': float(p_value),
            'psi': float(psi),
            'baseline_pitches': int(len(baseline)),
            'fresh_pitches': int(len(fresh)),
            'baseline_distribution': {
                k: float(v) for k, v in baseline_dist.to_dict().items()
            },
            'fresh_distribution': {
                k: float(v) for k, v in fresh_dist.to_dict().items()
            },
        }
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(report, indent=2))
        return report

    # Calculate pitch type distributions
    baseline_dist = get_pitch_distribution(baseline)
    fresh_dist    = get_pitch_distribution(fresh)

    print("\n=== Pitch Type Distributions ===")
    print(f"{'Pitch':<6} {'Baseline':>10} {'Fresh':>10} {'Delta':>10}")
    print("-" * 40)
    all_pitches = baseline_dist.index.union(fresh_dist.index)
    for pitch in sorted(all_pitches):
        b = baseline_dist.get(pitch, 0)
        f = fresh_dist.get(pitch, 0)
        print(f"{pitch:<6} {b:>10.3f} {f:>10.3f} {f-b:>+10.3f}")

    # Chi-squared test on pitch type distributions
    baseline_counts = baseline['pitch_type'].value_counts()
    fresh_counts    = fresh['pitch_type'].value_counts()
    common_pitches  = baseline_counts.index.intersection(fresh_counts.index)

    chi2, p_value = stats.chisquare(
        f_obs=fresh_counts[common_pitches],
        f_exp=baseline_counts[common_pitches] / baseline_counts[common_pitches].sum()
               * fresh_counts[common_pitches].sum()
    )

    # Population Stability Index
    psi = calculate_psi(baseline_dist, fresh_dist)

    # Drift decision
    drift_detected = p_value < DRIFT_THRESHOLD or psi >= 0.1
    retraining_recommended = p_value < DRIFT_THRESHOLD or psi >= 0.2

    print(f"\n=== Drift Analysis Results ===")
    print(f"Chi-squared statistic: {chi2:.4f}")
    print(f"P-value:               {p_value:.6f}")
    print(f"PSI:                   {psi:.4f}")
    print(f"Drift detected:        {drift_detected}")
    print(f"Retraining recommended: {retraining_recommended}")

    report = {
        'drift_detected': bool(drift_detected),
        'retraining_recommended': bool(retraining_recommended),
        'chi2_statistic': float(chi2),
        'p_value': float(p_value),
        'psi': float(psi),
        'baseline_pitches': int(len(baseline)),
        'fresh_pitches': int(len(fresh)),
        'baseline_distribution': {
            k: float(v) for k, v in baseline_dist.to_dict().items()
        },
        'fresh_distribution': {
            k: float(v) for k, v in fresh_dist.to_dict().items()
        },
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2))
    print(f"\nDrift report saved to {REPORT_PATH}")

    return report


if __name__ == '__main__':
    run()