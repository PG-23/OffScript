# OffScript

> Deriving MLB pitch selection theory from Statcast data — and identifying the pitchers who break the rules.

OffScript trains a machine learning model on pitch-by-pitch Statcast data to establish
a statistical baseline for "optimal" pitch selection. It then measures how individual
pitchers deviate from that baseline, determines whether those deviations are effective
or costly, and maps pitcher tendencies to batter vulnerability profiles — exposing which
batters are best positioned to exploit each pitcher's patterns.

## Project Status

| Phase | Description | Status |
|---|---|---|
| 1 | Data foundation — Statcast pipeline, EDA, data quality | ✅ Complete |
| 2 | Baseline theory model — XGBoost pitch selection classifier | ✅ Complete |
| 3 | Deviation analysis — per-pitcher deviation scoring and effectiveness | ✅ Complete |
| 4 | Batter vulnerability mapping — matchup engine and exploitability scores | ✅ Complete |
| 5 | API layer — FastAPI backend exposing model and matchup data | ✅ Complete |
| 6 | Deployment — Docker, GitHub Actions, Kubernetes, Railway | ✅ Complete |
| 7 | Monitoring — Prometheus metrics, Grafana dashboards, alert rules | ✅ Complete |
| 8 | Infrastructure as Code — Terraform provisioning for full Kubernetes stack | ✅ Complete |
| 9 | Azure Pipelines — dual CI/CD pipeline alongside GitHub Actions | ✅ Complete |
| 10 | AI Self-Healing Pipeline — Airflow DAG with drift detection and auto-retraining | ✅ Complete |

> All planned phases complete. The project continues to evolve —
> future additions may include a game layer and expanded pitcher roster.

## Key Findings

- An XGBoost classifier trained on game context features achieves **42.4% accuracy** and
  **48.2% balanced accuracy** predicting pitch type — well above the ~11% random baseline
  for 9 pitch classes, confirming that situational patterns are learnable
- **Pitcher identity accounts for 59.8%** of feature importance, confirming that individual
  arsenal and tendencies drive pitch selection more than any situational factor
- For **13 of 14 pitchers**, following the model recommendation produces better outcomes
  than deviating — validating the baseline pitch selection theory
- **Chris Sale** shows the most costly deviation pattern at **-10.74%** positive outcome
  differential when deviating vs following recommendations
- **Corbin Burnes** is the only pitcher where deviation consistently outperforms the model
  (+0.79%), suggesting strategic sophistication beyond what the baseline theory captures
- The matchup engine produces a **correlation of -0.363** between deviation cost and batter
  exploitability, confirming the engine correctly identifies vulnerable pitchers

## Live API

**Base URL:** https://offscript-production-ba5b.up.railway.app

| Endpoint | Description |
|---|---|
| [`/docs`](https://offscript-production-ba5b.up.railway.app/docs) | Interactive Swagger documentation |
| [`/health`](https://offscript-production-ba5b.up.railway.app/health) | API health check |
| [`/pitchers`](https://offscript-production-ba5b.up.railway.app/pitchers) | All pitcher deviation profiles |
| [`/recommend`](https://offscript-production-ba5b.up.railway.app/recommend) | Live pitch recommendation |

> Hosted on Railway. The first request may take 30-60 seconds
> if the service has been inactive.

## API

The OffScript API is built with FastAPI and exposes model inference
and analysis data as REST endpoints.

**Running locally:**
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```
Visit `http://localhost:8000/docs` for interactive Swagger documentation.

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | API health check |
| `/metrics` | GET | Prometheus metrics scrape endpoint |
| `/pitchers` | GET | All pitcher deviation profiles |
| `/pitchers/{name}` | GET | Specific pitcher profile |
| `/pitchers/{name}/arsenal` | GET | Pitcher pitch mix distribution |
| `/pitchers/{name}/deviations` | GET | Deviation substitution patterns |
| `/matchups/{pitcher}` | GET | Top batter matchups for a pitcher |
| `/matchups/{pitcher}/{batter}` | GET | Specific pitcher-batter matchup |
| `/recommend` | POST | Live pitch recommendation for a game situation |

## CI/CD

OffScript ships with two parallel CI/CD pipelines that both trigger
on every push to main.

### GitHub Actions

Defined in `.github/workflows/ci.yml`. Runs on Microsoft-hosted
Ubuntu runners.

| Step | Description |
|---|---|
| Install dependencies | Installs from requirements-api.txt |
| Run tests | pytest suite across all API endpoints |
| Build Docker image | Verifies container builds successfully |

### Azure Pipelines

Defined in `azure-pipelines.yml`. Runs on a self-hosted Windows
agent with Anaconda Python 3.11.

| Step | Description |
|---|---|
| Verify Python environment | Confirms Python and pip are available |
| Install dependencies | Installs from requirements-api.txt |
| Run pytest suite | Full test coverage with JUnit XML reporting |
| Publish test results | Visual test results dashboard in Azure DevOps |
| Build Docker image | Tagged with build ID for versioned artifact tracking |

## Monitoring

OffScript includes a full observability stack powered by Prometheus and Grafana,
providing real-time visibility into API health, request volume, error rates, and
response time distributions.

**Run the full stack locally:**
```bash
docker-compose up
```

| Service | URL | Description |
|---|---|---|
| API | http://localhost:8000 | FastAPI REST API |
| Metrics | http://localhost:8000/metrics | Raw Prometheus metrics |
| Prometheus | http://localhost:9090 | Metrics storage and alerting |
| Grafana | http://localhost:3000 | Monitoring dashboard (admin / offscript) |

### Dashboard Panels
- **Total API Requests** — cumulative request count since startup
- **Requests Per Minute** — real-time request rate time series
- **Request Rate by Endpoint** — per-endpoint traffic breakdown
- **Error Rate %** — percentage of 4xx and 5xx responses
- **95th Percentile Response Time** — latency distribution per endpoint
- **API Status** — live UP/DOWN health indicator

### Alert Rules
Three alert rules are configured in Prometheus:
- **OffScriptAPIDown** — fires if the API is unreachable for more than 1 minute
- **HighErrorRate** — fires if error rate exceeds 5% for 2 consecutive minutes
- **SlowResponseTime** — fires if p95 response time exceeds 2 seconds for 2 minutes

## Self-Healing Pipeline

OffScript includes an AI-powered self-healing pipeline that automatically
detects model drift and retrains the pitch selection model on fresh
Statcast data without human intervention.

**Run the Airflow stack:**
```bash
docker-compose -f airflow/docker-compose-airflow.yml up -d
```

Visit `http://localhost:8080` for the Airflow dashboard (admin / offscript).

### Pipeline Tasks

| Task | Description |
|---|---|
| data_ingestion | Pulls fresh Statcast data for all 14 pitchers via pybaseball |
| drift_detection | Chi-squared test and PSI analysis vs 2023-2024 baseline |
| model_retraining | XGBoost retrained on combined historical and fresh data |
| model_evaluation | Candidate vs current model on fresh data holdout set |
| model_deployment | Promotes candidate if improved, triggers Kubernetes rolling restart |

### Schedule
Runs automatically every Monday at 06:00 UTC.

### Key Finding From First Run (May 2026)
Significant pitch selection drift detected between 2023-2024 and 2025
seasons — fastball and cutter usage declined while slider and sinker
usage increased substantially. The pipeline correctly retained the
current model after determining the retrained candidate performed worse
on 2025 data, demonstrating intelligent deployment decisions rather
than blind auto-deployment.

## Docker

**Build the image:**
```bash
docker build -t offscript-api:latest .
```

**Run with Docker Compose:**
```bash
docker-compose up
```

**Run tests in container:**
```bash
docker-compose --profile test run offscript-tests
```

Visit `http://localhost:8000/docs` for interactive documentation.

> **Note:** The model file (~8 MB) is downloaded automatically from
> GitHub Releases during the build. Ensure internet access is available
> when building the image.

## Tech Stack

| Layer | Technology |
|---|---|
| Data retrieval | pybaseball, Statcast API |
| Data processing | pandas, numpy, pyarrow |
| Machine learning | XGBoost, scikit-learn, SHAP |
| Visualisation | matplotlib, seaborn |
| Notebook environment | JupyterLab |
| API | FastAPI, Pydantic |
| Monitoring | Prometheus, Grafana |
| CI/CD | GitHub Actions, Azure Pipelines |
| Infrastructure as Code | Terraform |
| Pipeline orchestration | Apache Airflow |
| Deployment | Docker, Kubernetes, Railway |

## Project Structure

```
OffScript/
├── airflow/
│   ├── dags/
│   │   └── offscript_retraining_dag.py     # Airflow DAG — orchestrates full retraining pipeline
│   ├── scripts/
│   │   ├── data_ingestion.py               # Task 1 — pulls fresh Statcast data via pybaseball
│   │   ├── drift_detection.py              # Task 2 — chi-squared and PSI drift analysis
│   │   ├── model_retraining.py             # Task 3 — retrains XGBoost on combined data
│   │   ├── model_evaluation.py             # Task 4 — evaluates candidate vs current model
│   │   ├── model_deployment.py             # Task 5 — promotes model and restarts Kubernetes
│   │   └── __init__.py
│   ├── Dockerfile.airflow                  # Custom Airflow image with pipeline dependencies
│   ├── docker-compose-airflow.yml          # Airflow stack — webserver, scheduler, postgres
│   └── requirements-airflow.txt            # Pipeline script dependencies
├── api/
│   ├── models/
│   │   └── schemas.py                      # Pydantic request and response schemas
│   ├── routers/
│   │   ├── matchups.py                     # GET /matchups/ endpoints
│   │   ├── pitchers.py                     # GET /pitchers/ endpoints
│   │   └── recommend.py                    # POST /recommend/ endpoint
│   ├── tests/
│   │   ├── test_matchups.py
│   │   ├── test_pitchers.py
│   │   └── test_recommend.py
│   ├── config.py                           # DataStore — loads models and data at startup
│   ├── main.py                             # FastAPI application entry point
│   └── startup.py                          # Model download utility
├── data/
│   ├── deploy/                             # Minimal parquet subset baked into Docker image
│   └── processed/                          # Full parquet files — local development only (gitignored)
├── k8s/
│   ├── configmap.yml                       # Kubernetes environment configuration
│   ├── deployment.yml                      # Kubernetes deployment manifest
│   ├── namespace.yml                       # Kubernetes namespace definition
│   └── service.yml                         # Kubernetes service and ingress
├── models/                                 # Trained model artifacts (gitignored)
├── monitoring/
│   ├── prometheus/
│   │   ├── prometheus.yml                  # Prometheus scrape and alerting configuration
│   │   └── alert_rules.yml                 # Alert rule definitions
│   └── grafana/
│       ├── dashboards/
│       │   └── offscript_dashboard.json    # Pre-built API monitoring dashboard
│       └── provisioning/
│           ├── datasources/                # Grafana to Prometheus connection
│           └── dashboards/                 # Dashboard auto-load configuration
├── notebooks/
│   ├── 01_initial_exploration.ipynb
│   ├── 02_data_collection.ipynb
│   ├── 03_exploratory_analysis.ipynb
│   ├── 04_data_quality.ipynb
│   ├── 05_baseline_model.ipynb
│   ├── 06_deviation_analysis.ipynb
│   ├── 07_batter_data_collection.ipynb
│   ├── 08_matchup_analysis.ipynb
│   └── 09_deployment_data_prep.ipynb
├── reports/
│   └── figures/                            # All saved visualisations
├── src/
│   └── pitch_analysis.py                   # Shared utility functions used across notebooks
├── terraform/
│   └── kubernetes/
│       ├── versions.tf                     # Provider and Terraform version requirements
│       ├── variables.tf                    # Input variables with defaults
│       ├── main.tf                         # Resource definitions for full stack
│       └── outputs.tf                      # Output values displayed after apply
├── .dockerignore
├── .github/
│   └── workflows/
│       └── ci.yml                          # GitHub Actions CI pipeline
├── azure-pipelines.yml                     # Azure Pipelines CI configuration
├── docker-compose.yml                      # Local Docker development environment
├── Dockerfile                              # Production container definition
├── environment.yml                         # Conda environment for local notebook development
├── requirements-api.txt                    # Pip dependencies for Docker and CI
└── README.md
```

## Setup

```bash
# Clone the repository
git clone https://github.com/PG-23/offscript.git
cd offscript

# Create and activate the Conda environment
conda env create -f environment.yml
conda activate offscript

# Launch JupyterLab
jupyter lab
```

Run the notebooks in order (01 through 08). Each notebook documents its input
and output files in the header cell.

## Data Source

MLB Statcast pitch-by-pitch data via [pybaseball](https://github.com/jldbc/pybaseball),
covering the 2023 and 2024 regular seasons and postseason for a curated roster of
14 pitchers across four archetypes: Power Arms, Finesse, Ground Ball, and Deviation
Candidates.

## Pitcher Roster

| Archetype | Pitchers |
|---|---|
| Power Arms | Gerrit Cole, Spencer Strider, Corbin Burnes |
| Finesse | Zack Wheeler, Kyle Hendricks, Chris Sale |
| Ground Ball | Logan Webb, Framber Valdez, Marcus Stroman |
| Veterans | Max Scherzer, Justin Verlander |
| Deviation Candidates | Yusei Kikuchi, Dylan Cease, Nestor Cortes |

## Author

Patrick Guinn — [LinkedIn](https://www.linkedin.com/in/patrick-guinn/) | [GitHub](https://github.com/PG-23)