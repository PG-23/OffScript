# OffScript

> Deriving MLB pitch selection theory from Statcast data — and identifying the pitchers who break the rules.

OffScript trains a machine learning model on pitch-by-pitch Statcast data to establish
a statistical baseline for "optimal" pitch selection. It then measures how individual
pitchers deviate from that baseline, determines whether those deviations are effective
or costly, and maps pitcher tendencies to batter vulnerability profiles — exposing which
batters are best positioned to exploit each pitcher's patterns.

## Project Status

🔵 **Phase 6 — Deployment (In Progress)**

| Phase | Description | Status |
|---|---|---|
| 1 | Data foundation — Statcast pipeline, EDA, data quality | ✅ Complete |
| 2 | Baseline theory model — XGBoost pitch selection classifier | ✅ Complete |
| 3 | Deviation analysis — per-pitcher deviation scoring and effectiveness | ✅ Complete |
| 4 | Batter vulnerability mapping — matchup engine and exploitability scores | ✅ Complete |
| 5 | API layer — FastAPI backend exposing model and matchup data | ✅ Complete |
| 6 | Deployment — Docker, CI/CD, Kubernetes | 🔵 In Progress |

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

## Tech Stack

| Layer | Technology |
|---|---|
| Data retrieval | pybaseball, Statcast API |
| Data processing | pandas, numpy, pyarrow |
| Machine learning | XGBoost, scikit-learn, SHAP |
| Visualisation | matplotlib, seaborn |
| Notebook environment | JupyterLab |
| API (Phase 5) | FastAPI, Pydantic |
| Deployment (Phase 6) | Docker, GitHub Actions, Kubernetes |

## Project Structure

```
offscript/
├── data/
│   ├── processed/          # Parquet files produced by each phase
│   └── raw/                # Raw Statcast exports (gitignored)
├── models/                 # Trained model artifacts (gitignored)
├── notebooks/
│   ├── 01_initial_exploration.ipynb
│   ├── 02_data_collection.ipynb
│   ├── 03_exploratory_analysis.ipynb
│   ├── 04_data_quality.ipynb
│   ├── 05_baseline_model.ipynb
│   ├── 06_deviation_analysis.ipynb
│   ├── 07_batter_data_collection.ipynb
│   └── 08_matchup_analysis.ipynb
├── reports/
│   └── figures/            # All saved visualisations
├── src/
│   └── pitch_analysis.py   # Shared utility functions used across notebooks
├── environment.yml
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
15 pitchers across four archetypes: Power Arms, Finesse, Ground Ball, and Deviation
Candidates.

## Pitcher Roster

| Archetype | Pitchers |
|---|---|
| Power Arms | Gerrit Cole, Spencer Strider, Corbin Burnes |
| Finesse | Zack Wheeler, Kyle Hendricks, Chris Sale |
| Ground Ball | Logan Webb, Framber Valdez, Marcus Stroman |
| Veterans | Max Scherzer, Justin Verlander |
| Deviation Candidates | Yusei Kikuchi, Dylan Cease, Joe Ryan, Nestor Cortes |

## Author

Patrick Guinn — [LinkedIn](https://www.linkedin.com/in/patrick-guinn/) | [GitHub](https://github.com/PG-23)