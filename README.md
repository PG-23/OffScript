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

> Active development continues. Planned additions include Azure Pipelines 
> integration and an AI-powered self-healing pipeline.

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
| `/pitchers` | GET | All pitcher deviation profiles |
| `/pitchers/{name}` | GET | Specific pitcher profile |
| `/pitchers/{name}/arsenal` | GET | Pitcher pitch mix distribution |
| `/pitchers/{name}/deviations` | GET | Deviation substitution patterns |
| `/matchups/{pitcher}` | GET | Top batter matchups for a pitcher |
| `/matchups/{pitcher}/{batter}` | GET | Specific pitcher-batter matchup |
| `/recommend` | POST | Live pitch recommendation for a game situation |

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
| Deployment | Docker, GitHub Actions, Kubernetes |
| Infrastructure as Code | Terraform |

## Project Structure

```
offscript/
├── api/
│   ├── models/
│   │   └── schemas.py          # Pydantic request and response schemas
│   ├── routers/
│   │   ├── matchups.py         # GET /matchups/ endpoints
│   │   ├── pitchers.py         # GET /pitchers/ endpoints
│   │   └── recommend.py        # POST /recommend/ endpoint
│   ├── tests/
│   │   ├── test_matchups.py
│   │   ├── test_pitchers.py
│   │   └── test_recommend.py
│   ├── config.py               # DataStore — loads models and data at startup
│   ├── main.py                 # FastAPI application entry point
│   └── startup.py              # Model download utility
├── data/
│   ├── deploy/                 # Minimal parquet subset baked into Docker image
│   └── processed/              # Full parquet files — local development only (gitignored)
├── k8s/
│   ├── configmap.yml           # Kubernetes environment configuration
│   ├── deployment.yml          # Kubernetes deployment manifest
│   ├── namespace.yml           # Kubernetes namespace definition
│   └── service.yml             # Kubernetes service and ingress
├── models/                     # Trained model artifacts (gitignored)
├── monitoring/
│   ├── prometheus/
│   │   └── prometheus.yml      # Prometheus scrape and alerting configuration
|   |   └── alert_rules.yml     # Alert rule definitions
│   └── grafana/
│       ├── dashboards/                   # Dashboard JSON files
|       |   └── offscript_dashboard.json  # Pre-built API monitoring dashboard
│       └── provisioning/
│           ├── datasources/    # Grafana to Prometheus connection
│           └── dashboards/     # Dashboard auto-load configuration
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
│   └── figures/                # All saved visualisations
├── src/
│   └── pitch_analysis.py       # Shared utility functions used across notebooks
├── terraform/
│   └── kubernetes/
│       ├── versions.tf         # Provider and Terraform version requirements
│       ├── variables.tf        # Input variables with defaults
│       ├── main.tf             # Resource definitions for full stack
│       └── outputs.tf          # Output values displayed after apply
├── .dockerignore
├── .github/
│   └── workflows/
│       └── ci.yml              # CI pipeline — test and Docker build on push
├── docker-compose.yml          # Local Docker development environment
├── Dockerfile                  # Production container definition
├── environment.yml             # Conda environment for local notebook development
├── requirements-api.txt        # Pip dependencies for Docker and CI
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