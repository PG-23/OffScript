# api/config.py

from pathlib import Path
import joblib
import pandas as pd

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data' / 'processed'
MODELS_DIR = BASE_DIR / 'models'

# Data file paths
PITCHER_PROFILES_PATH = DATA_DIR / 'pitcher_profiles.parquet'
MATCHUP_SCORES_PATH = DATA_DIR / 'matchup_scores.parquet'
DEVIATION_EFFECTIVENESS_PATH = DATA_DIR / 'deviation_effectiveness.parquet'
BATTER_VULNERABILITY_PATH = DATA_DIR / 'batter_vulnerability.parquet'
PITCHER_DATA_PATH = DATA_DIR / 'pitcher_data_with_recommendations.parquet'

# Model file paths
MODEL_PATH = MODELS_DIR / 'baseline_pitch_model.pkl'
LABEL_ENCODER_PATH = MODELS_DIR / 'label_encoder.pkl'
PITCHER_ENCODER_PATH = MODELS_DIR / 'pitcher_encoder.pkl'

class DataStore:
    """
    Centralized data and model loader.
    Loads everything once at startup and holds in memory.
    Avoids reloading on every request.
    """
    def __init__(self):
        print("Loading models...")
        self.model = joblib.load(MODEL_PATH)
        self.label_encoder = joblib.load(LABEL_ENCODER_PATH)
        self.pitcher_encoder = joblib.load(PITCHER_ENCODER_PATH)

        print("Loading data...")
        self.pitcher_profiles = pd.read_parquet(PITCHER_PROFILES_PATH)
        self.matchup_scores = pd.read_parquet(MATCHUP_SCORES_PATH)
        self.deviation_effectiveness = pd.read_parquet(
            DEVIATION_EFFECTIVENESS_PATH
        )
        self.batter_vulnerability = pd.read_parquet(
            BATTER_VULNERABILITY_PATH
        )
        self.pitcher_data = pd.read_parquet(PITCHER_DATA_PATH)

        print("DataStore ready")

    def get_pitcher_names(self):
        return sorted(self.pitcher_profiles['pitcher_name'].tolist())

    def get_pitcher_profile(self, name):
        result = self.pitcher_profiles[
            self.pitcher_profiles['pitcher_name'] == name
        ]
        return result.iloc[0].to_dict() if len(result) > 0 else None

# Single global instance loaded at startup
store = DataStore()