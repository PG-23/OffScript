# OffScript

> Deriving MLB pitch selection theory from Statcast data — and analyzing the pitchers who break the rules.

## Overview
OffScript is a data-driven analysis system built on MLB Statcast pitch-by-pitch data. 
The project aims to derive a generalized pitch selection theory and identify pitchers 
who deviate from optimal selection patterns, exploring why those deviations occur and 
whether they are effective.

## Project Goals
- Build a clean Statcast data pipeline for multiple pitchers and seasons
- Derive a baseline pitch selection theory optimized for outcomes
- Identify and analyze pitcher deviation patterns from optimal selection
- Map pitcher tendencies to batter vulnerability profiles
- Expose findings via API for downstream consumption

## Project Status
🔵 Phase 5 — API Layer (In Progress)

## Tech Stack
- Python 3.11
- pybaseball, pandas, matplotlib, seaborn
- Jupyter Notebook
- (Planned) PostgreSQL, scikit-learn, FastAPI, Docker, Kubernetes

## Setup
```bash
conda env create -f environment.yml
conda activate offscript
```

## Data Source
MLB Statcast data via [pybaseball](https://github.com/jldbc/pybaseball)

## Project Phases
- [x] Phase 1 — Data Foundation
- [x] Phase 2 — Baseline Theory Model
- [x] Phase 3 — Deviation Analysis
- [x] Phase 4 — Batter Vulnerability Mapping
- [ ] Phase 5 — API Layer
- [ ] Phase 6 — Deployment

## Author
Patrick Guinn — [LinkedIn](https://www.linkedin.com/in/patrick-guinn/) | [GitHub](https://github.com/PG-23)
