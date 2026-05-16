# api/config.py

from pathlib import Path
import os
import joblib
import pandas as pd

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data' / 'processed'
DEPLOY_DATA_DIR = BASE_DIR / 'data' / 'deploy'
MODELS_DIR = BASE_DIR / 'models'

# Model file paths
MODEL_PATH = MODELS_DIR / 'baseline_pitch_model.pkl'
LABEL_ENCODER_PATH = MODELS_DIR / 'label_encoder.pkl'
PITCHER_ENCODER_PATH = MODELS_DIR / 'pitcher_encoder.pkl'

def _get_data_path(deploy_name, processed_name=None):
    """
    Return deploy path if it exists, otherwise fall back to processed path.
    This allows local development to use full data while deployment
    uses the committed minimal subset automatically.
    """
    deploy_path = DEPLOY_DATA_DIR / deploy_name
    if deploy_path.exists():
        return deploy_path
    processed_file = processed_name or deploy_name
    return DATA_DIR / processed_file

# Data file paths — prefer deploy data, fall back to processed data
PITCHER_PROFILES_PATH = _get_data_path('pitcher_profiles.parquet')
MATCHUP_SCORES_PATH = _get_data_path('matchup_scores.parquet')
DEVIATION_EFFECTIVENESS_PATH = _get_data_path('deviation_effectiveness.parquet')
BATTER_VULNERABILITY_PATH = _get_data_path('batter_vulnerability.parquet')
PITCHER_DATA_PATH = _get_data_path(
    'pitcher_data.parquet',
    'pitcher_data_with_recommendations.parquet'
)

class DataStore:
    """
    Centralized data and model loader.
    Loads everything once at startup and holds in memory.
    Falls back to mock data in CI/testing environments.
    """
    def __init__(self):
        testing = os.environ.get('TESTING', 'false').lower() == 'true'
        ci = os.environ.get('CI', 'false').lower() == 'true'
        models_exist = MODEL_PATH.exists()

        if testing or ci or not models_exist:
            print("CI/Testing environment detected — loading mock data")
            self._load_mock_data()
        else:
            print("Loading models...")
            self._load_real_data()

    def _load_real_data(self):
        """Load real models and data for production use."""
        self.model = joblib.load(MODEL_PATH)
        self.label_encoder = joblib.load(LABEL_ENCODER_PATH)
        self.pitcher_encoder = joblib.load(PITCHER_ENCODER_PATH)

        print("Loading data...")
        print(f"  Profiles:      {PITCHER_PROFILES_PATH}")
        print(f"  Matchups:      {MATCHUP_SCORES_PATH}")
        print(f"  Pitcher data:  {PITCHER_DATA_PATH}")

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

    def _load_mock_data(self):
        """Load minimal mock data for CI and testing environments."""
        import numpy as np
        from sklearn.preprocessing import LabelEncoder
        from unittest.mock import MagicMock

        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([3])
        mock_model.predict_proba.return_value = np.array([[
            0.05, 0.05, 0.10, 0.35, 0.02,
            0.03, 0.15, 0.20, 0.05
        ]])
        self.model = mock_model

        le = LabelEncoder()
        le.fit(['CH', 'CU', 'FC', 'FF', 'FS', 'KC', 'SI', 'SL', 'ST'])
        self.label_encoder = le

        pe = LabelEncoder()
        pe.fit([
            'Chris Sale', 'Corbin Burnes', 'Dylan Cease',
            'Framber Valdez', 'Gerrit Cole', 'Justin Verlander',
            'Kyle Hendricks', 'Logan Webb', 'Marcus Stroman',
            'Max Scherzer', 'Nestor Cortes', 'Spencer Strider',
            'Yusei Kikuchi', 'Zack Wheeler'
        ])
        self.pitcher_encoder = pe

        self.pitcher_profiles = pd.DataFrame([
            {
                'pitcher_name': 'Gerrit Cole',
                'total_pitches': 5248,
                'deviation_score': 63.9,
                'deviation_positive_rate': 26.93,
                'followed_positive_rate': 30.49,
                'deviation_advantage': -3.99,
                'two_strike_dev_cost': -0.45,
                'arsenal_size': 6,
                'deviation_rank': 1
            },
            {
                'pitcher_name': 'Chris Sale',
                'total_pitches': 4495,
                'deviation_score': 53.4,
                'deviation_positive_rate': 27.14,
                'followed_positive_rate': 37.88,
                'deviation_advantage': -10.74,
                'two_strike_dev_cost': -10.46,
                'arsenal_size': 4,
                'deviation_rank': 5
            }
        ])

        self.matchup_scores = pd.DataFrame([
            {
                'pitcher_name': 'Chris Sale',
                'batter_id': 605141,
                'batter_name': 'mookie betts',
                'stand': 'R',
                'matchup_score': 61.30
            },
            {
                'pitcher_name': 'Gerrit Cole',
                'batter_id': 457759,
                'batter_name': 'justin turner',
                'stand': 'R',
                'matchup_score': 58.20
            }
        ])

        self.deviation_effectiveness = pd.DataFrame(
            columns=['pitcher_name', 'deviation_positive_rate',
                     'followed_positive_rate', 'deviation_advantage']
        )
        self.batter_vulnerability = pd.DataFrame(
            columns=['batter', 'batter_name', 'stand',
                     'pitch_type', 'vulnerability_score']
        )
        self.pitcher_data = pd.DataFrame([
            {
                'pitcher_name': 'Gerrit Cole',
                'pitch_type': 'FF',
                'recommended_pitch': 'FF',
                'followed_recommendation': True,
                'balls': 0,
                'strikes': 0
            },
            {
                'pitcher_name': 'Gerrit Cole',
                'pitch_type': 'SL',
                'recommended_pitch': 'FF',
                'followed_recommendation': False,
                'balls': 0,
                'strikes': 2
            },
            {
                'pitcher_name': 'Gerrit Cole',
                'pitch_type': 'KC',
                'recommended_pitch': 'KC',
                'followed_recommendation': True,
                'balls': 1,
                'strikes': 2
            },
            {
                'pitcher_name': 'Chris Sale',
                'pitch_type': 'FF',
                'recommended_pitch': 'SL',
                'followed_recommendation': False,
                'balls': 0,
                'strikes': 0
            },
            {
                'pitcher_name': 'Chris Sale',
                'pitch_type': 'SL',
                'recommended_pitch': 'SL',
                'followed_recommendation': True,
                'balls': 0,
                'strikes': 2
            }
        ])

        print("Mock DataStore ready")

    def get_pitcher_names(self):
        return sorted(self.pitcher_profiles['pitcher_name'].tolist())

    def get_pitcher_profile(self, name):
        result = self.pitcher_profiles[
            self.pitcher_profiles['pitcher_name'] == name
        ]
        return result.iloc[0].to_dict() if len(result) > 0 else None

# Single global instance loaded at startup
store = DataStore()