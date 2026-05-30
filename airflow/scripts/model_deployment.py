# airflow/scripts/model_deployment.py
"""
Model deployment script for OffScript retraining pipeline.

If the evaluation report recommends deployment, replaces the
production model with the candidate model and triggers a
Kubernetes rolling restart of the API deployment.

Called by the Airflow DAG as Task 5 of 5.
"""

import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────

CANDIDATE_DIR      = Path('/opt/airflow/models/candidate')
PRODUCTION_DIR     = Path('/opt/airflow/models')
EVAL_REPORT_PATH   = Path('/opt/airflow/data/fresh/evaluation_report.json')
DRIFT_REPORT_PATH  = Path('/opt/airflow/data/fresh/drift_report.json')
DEPLOY_LOG_PATH    = Path('/opt/airflow/data/fresh/deployment_log.json')

MODEL_FILES = [
    'baseline_pitch_model.pkl',
    'label_encoder.pkl',
    'pitcher_encoder.pkl'
]


def load_report(path: Path) -> dict:
    """Load a JSON report file."""
    if not path.exists():
        raise FileNotFoundError(f"Report not found: {path}")
    return json.loads(path.read_text())


def promote_candidate_model() -> None:
    """Copy candidate model files to production directory."""
    print("Promoting candidate model to production...")
    for filename in MODEL_FILES:
        src = CANDIDATE_DIR / filename
        dst = PRODUCTION_DIR / filename
        if src.exists():
            shutil.copy2(src, dst)
            print(f"  Copied {filename}")
        else:
            print(f"  WARNING: {filename} not found in candidate directory")


def trigger_kubernetes_restart() -> bool:
    """
    Trigger a rolling restart of the OffScript API deployment.
    Returns True if successful, False otherwise.
    """
    print("\nTriggering Kubernetes rolling restart...")
    try:
        result = subprocess.run(
            [
                'kubectl', 'rollout', 'restart',
                'deployment/offscript-api',
                '-n', 'offscript'
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"  Rolling restart triggered successfully")
            print(f"  {result.stdout.strip()}")
            return True
        else:
            print(f"  WARNING: kubectl returned non-zero exit code")
            print(f"  {result.stderr.strip()}")
            return False
    except FileNotFoundError:
        print("  WARNING: kubectl not found — skipping Kubernetes restart")
        print("  Model files updated but API restart must be done manually")
        return False
    except subprocess.TimeoutExpired:
        print("  WARNING: kubectl command timed out")
        return False


def run():
    """Main entry point — deploys or skips based on evaluation report."""
    print("=" * 60)
    print("OffScript Model Deployment")
    print("=" * 60)

    # Load reports
    eval_report  = load_report(EVAL_REPORT_PATH)
    drift_report = load_report(DRIFT_REPORT_PATH)

    deploy = eval_report.get('deploy_candidate', False)
    improvement = eval_report.get('improvement', 0)

    print(f"Deployment decision: {'DEPLOY' if deploy else 'SKIP'}")
    print(f"Improvement over current model: {improvement:+.3f}")

    deployment_log = {
        'timestamp': datetime.utcnow().isoformat(),
        'deployed': False,
        'reason': None,
        'improvement': improvement,
        'drift_detected': drift_report.get('drift_detected', False),
        'kubernetes_restart': False
    }

    if deploy:
        print("\nDeploying candidate model...")
        promote_candidate_model()
        k8s_success = trigger_kubernetes_restart()

        deployment_log['deployed'] = True
        deployment_log['reason'] = 'candidate_model_improved'
        deployment_log['kubernetes_restart'] = k8s_success

        print("\n✓ Deployment complete")
        print(f"  Model improvement: {improvement:+.3f} balanced accuracy")
        print(f"  Kubernetes restart: {'success' if k8s_success else 'manual required'}")
    else:
        deployment_log['reason'] = 'candidate_did_not_improve'
        print("\nSkipping deployment — current model performs better")
        print(f"  Current model retained")

    DEPLOY_LOG_PATH.write_text(json.dumps(deployment_log, indent=2))
    print(f"\nDeployment log saved to {DEPLOY_LOG_PATH}")

    return deployment_log


if __name__ == '__main__':
    run()