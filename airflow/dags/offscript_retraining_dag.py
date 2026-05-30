# airflow/dags/offscript_retraining_dag.py
"""
OffScript Retraining DAG

Orchestrates the full self-healing ML pipeline for the OffScript
pitch selection model. Runs weekly to detect distribution drift
in pitch selection patterns and retrain the XGBoost classifier
on combined historical and fresh Statcast data.

Pipeline:
    data_ingestion → drift_detection → model_retraining
    → model_evaluation → model_deployment

Schedule: Weekly on Mondays at 06:00 UTC
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.python import ShortCircuitOperator

import sys
sys.path.insert(0, '/opt/airflow')

from scripts.data_ingestion import run as ingest_data
from scripts.drift_detection import run as detect_drift
from scripts.model_retraining import run as retrain_model
from scripts.model_evaluation import run as evaluate_model
from scripts.model_deployment import run as deploy_model

# ── DAG Default Arguments ─────────────────────────────────────────────────

default_args = {
    'owner': 'offscript',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# ── DAG Definition ────────────────────────────────────────────────────────

with DAG(
    dag_id='offscript_model_retraining',
    default_args=default_args,
    description=(
        'Weekly self-healing pipeline — detects pitch selection drift '
        'and retrains the XGBoost model on fresh Statcast data'
    ),
    schedule_interval='0 6 * * 1',  # Every Monday at 06:00 UTC
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['offscript', 'mlops', 'retraining'],
) as dag:

    # ── Task 1: Pull fresh Statcast data ──────────────────────────────────
    task_ingest = PythonOperator(
        task_id='data_ingestion',
        python_callable=ingest_data,
        doc_md="""
        **Data Ingestion**
        Pulls fresh 2025 Statcast pitch-by-pitch data for all 14 pitchers
        using pybaseball. Saves combined dataset to data/fresh/.
        """,
    )

    # ── Task 2: Detect distribution drift ────────────────────────────────
    task_drift = PythonOperator(
        task_id='drift_detection',
        python_callable=detect_drift,
        doc_md="""
        **Drift Detection**
        Compares 2025 pitch type distribution against 2023-2024 baseline
        using chi-squared test and Population Stability Index (PSI).
        Saves drift report to data/fresh/.
        """,
    )

    # ── Task 3: Retrain model on combined data ────────────────────────────
    task_retrain = PythonOperator(
        task_id='model_retraining',
        python_callable=retrain_model,
        doc_md="""
        **Model Retraining**
        Combines 2023-2024 baseline data with fresh 2025 data and retrains
        the XGBoost pitch selection classifier. Saves candidate model to
        models/candidate/.
        """,
    )

    # ── Task 4: Evaluate candidate vs current model ───────────────────────
    task_evaluate = PythonOperator(
        task_id='model_evaluation',
        python_callable=evaluate_model,
        doc_md="""
        **Model Evaluation**
        Evaluates both the current production model and the candidate model
        on fresh data. Recommends deployment if candidate achieves equal
        or better balanced accuracy.
        """,
    )

    # ── Task 5: Deploy if improved ────────────────────────────────────────
    task_deploy = PythonOperator(
        task_id='model_deployment',
        python_callable=deploy_model,
        doc_md="""
        **Model Deployment**
        Promotes the candidate model to production if evaluation recommends
        it. Triggers a Kubernetes rolling restart of the API deployment
        to load the new model without downtime.
        """,
    )

    # ── Task Dependencies ─────────────────────────────────────────────────
    # Linear pipeline — each task depends on the previous succeeding
    task_ingest >> task_drift >> task_retrain >> task_evaluate >> task_deploy