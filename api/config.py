# api/config.py
"""Application configuration, path resolution, and data store.

Loads all models and analytical datasets once at startup and holds them
in a single global DataStore instance. In CI and testing environments,
minimal mock data is loaded instead so tests run without requiring the
full model artifacts or parquet files.
"""

import os
from pathlib import Path

import joblib
import pandas as pd

# ── Path configuration ────────────────────────────────────────────────────

BASE_DIR        = Path(__file__).resolve().parent.parent
DATA_DIR        = BASE_DIR / "data" / "processed"
DEPLOY_DATA_DIR = BASE_DIR / "data" / "deploy"
MODELS_DIR      = BASE_DIR / "models"

MODEL_PATH           = MODELS_DIR / "baseline_pitch_model.pkl"
LABEL_ENCODER_PATH   = MODELS_DIR / "label_encoder.pkl"
PITCHER_ENCODER_PATH = MODELS_DIR / "pitcher_encoder.pkl"


def _get_data_path(deploy_name: str, processed_name: str | None = None) -> Path:
    """Resolve the correct data file path for the current environment.

    Prefers the deploy data subset (committed to the repo, used in Docker)
    over the full processed data (local development only). This allows the
    same code to run in both environments without configuration changes.

    Args:
        deploy_name: Filename within data/deploy/.
        processed_name: Filename within data/processed/ if different from
            deploy_name. Defaults to deploy_name if not provided.

    Returns:
        Path to the deploy file if it exists, otherwise the processed path.
    """
    deploy_path = DEPLOY_DATA_DIR / deploy_name
    if deploy_path.exists():
        return deploy_path
    return DATA_DIR / (processed_name or deploy_name)


# Data file paths — deploy subset takes priority over full processed data
PITCHER_PROFILES_PATH       = _get_data_path("pitcher_profiles.parquet")
MATCHUP_SCORES_PATH         = _get_data_path("matchup_scores.parquet")
DEVIATION_EFFECTIVENESS_PATH = _get_data_path("deviation_effectiveness.parquet")
BATTER_VULNERABILITY_PATH   = _get_data_path("batter_vulnerability.parquet")
PITCHER_DATA_PATH           = _get_data_path(
    "pitcher_data.parquet",
    "pitcher_data_with_recommendations.parquet",
)


# ── Data store ────────────────────────────────────────────────────────────

class DataStore:
    """Centralized loader for all models and analytical datasets.

    Loads everything once at startup and holds it in memory for the
    lifetime of the process. In CI and testing environments (detected
    via TESTING or CI environment variables, or missing model files),
    minimal mock data is loaded instead.

    Attributes:
        model: Trained XGBoost pitch selection classifier.
        label_encoder: LabelEncoder mapping pitch type codes to integers.
        pitcher_encoder: LabelEncoder mapping pitcher names to integers.
        pitcher_profiles: DataFrame of per-pitcher deviation profiles.
        matchup_scores: DataFrame of pitcher-batter exploitation scores.
        deviation_effectiveness: DataFrame of deviation outcome rates.
        batter_vulnerability: DataFrame of batter vulnerability scores.
        pitcher_data: Pitch-level DataFrame with recommendations attached.
    """

    def __init__(self) -> None:
        testing      = os.environ.get("TESTING", "false").lower() == "true"
        ci           = os.environ.get("CI", "false").lower() == "true"
        models_exist = MODEL_PATH.exists()

        if testing or ci or not models_exist:
            print("CI/Testing environment detected — loading mock data")
            self._load_mock_data()
        else:
            print("Loading models and data...")
            self._load_real_data()

    def _load_real_data(self) -> None:
        """Load production models and parquet datasets."""
        self.model           = joblib.load(MODEL_PATH)
        self.label_encoder   = joblib.load(LABEL_ENCODER_PATH)
        self.pitcher_encoder = joblib.load(PITCHER_ENCODER_PATH)

        print(f"  Profiles:     {PITCHER_PROFILES_PATH}")
        print(f"  Matchups:     {MATCHUP_SCORES_PATH}")
        print(f"  Pitcher data: {PITCHER_DATA_PATH}")

        self.pitcher_profiles        = pd.read_parquet(PITCHER_PROFILES_PATH)
        self.matchup_scores          = pd.read_parquet(MATCHUP_SCORES_PATH)
        self.deviation_effectiveness = pd.read_parquet(DEVIATION_EFFECTIVENESS_PATH)
        self.batter_vulnerability    = pd.read_parquet(BATTER_VULNERABILITY_PATH)
        self.pitcher_data            = pd.read_parquet(PITCHER_DATA_PATH)

        print("DataStore ready")

    def _load_mock_data(self) -> None:
        """Load minimal mock data for CI and testing environments.

        Mock data covers two pitchers (Gerrit Cole, Chris Sale) with enough
        rows to exercise all API endpoints without requiring real model
        artifacts or parquet files.
        """
        import numpy as np
        from unittest.mock import MagicMock
        from sklearn.preprocessing import LabelEncoder

        # Mock model returns a fixed probability distribution
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([3])
        mock_model.predict_proba.return_value = np.array([[
            0.05, 0.05, 0.10, 0.35, 0.02,
            0.03, 0.15, 0.20, 0.05,
        ]])
        self.model = mock_model

        le = LabelEncoder()
        le.fit(["CH", "CU", "FC", "FF", "FS", "KC", "SI", "SL", "ST"])
        self.label_encoder = le

        pe = LabelEncoder()
        pe.fit([
            "Chris Sale", "Corbin Burnes", "Dylan Cease",
            "Framber Valdez", "Gerrit Cole", "Justin Verlander",
            "Kyle Hendricks", "Logan Webb", "Marcus Stroman",
            "Max Scherzer", "Nestor Cortes", "Spencer Strider",
            "Yusei Kikuchi", "Zack Wheeler",
        ])
        self.pitcher_encoder = pe

        self.pitcher_profiles = pd.DataFrame([
            {
                "pitcher_name":           "Gerrit Cole",
                "total_pitches":          5248,
                "deviation_score":        63.9,
                "deviation_positive_rate": 26.93,
                "followed_positive_rate": 30.49,
                "deviation_advantage":    -3.99,
                "two_strike_dev_cost":    -0.45,
                "arsenal_size":           6,
                "deviation_rank":         1,
            },
            {
                "pitcher_name":           "Chris Sale",
                "total_pitches":          4495,
                "deviation_score":        53.4,
                "deviation_positive_rate": 27.14,
                "followed_positive_rate": 37.88,
                "deviation_advantage":    -10.74,
                "two_strike_dev_cost":    -10.46,
                "arsenal_size":           4,
                "deviation_rank":         5,
            },
        ])

        self.matchup_scores = pd.DataFrame([
            {
                "pitcher_name":  "Chris Sale",
                "batter_id":     605141,
                "batter_name":   "Mookie Betts",
                "stand":         "R",
                "matchup_score": 61.30,
            },
            {
                "pitcher_name":  "Gerrit Cole",
                "batter_id":     457759,
                "batter_name":   "Justin Turner",
                "stand":         "R",
                "matchup_score": 58.20,
            },
        ])

        self.deviation_effectiveness = pd.DataFrame(
            columns=["pitcher_name", "deviation_positive_rate",
                     "followed_positive_rate", "deviation_advantage"]
        )
        self.batter_vulnerability = pd.DataFrame(
            columns=["batter", "batter_name", "stand",
                     "pitch_type", "vulnerability_score"]
        )
        self.pitcher_data = pd.DataFrame([
            {
                "pitcher_name":          "Gerrit Cole",
                "pitch_type":            "FF",
                "recommended_pitch":     "FF",
                "followed_recommendation": True,
                "balls":   0,
                "strikes": 0,
            },
            {
                "pitcher_name":          "Gerrit Cole",
                "pitch_type":            "SL",
                "recommended_pitch":     "FF",
                "followed_recommendation": False,
                "balls":   0,
                "strikes": 2,
            },
            {
                "pitcher_name":          "Gerrit Cole",
                "pitch_type":            "KC",
                "recommended_pitch":     "KC",
                "followed_recommendation": True,
                "balls":   1,
                "strikes": 2,
            },
            {
                "pitcher_name":          "Chris Sale",
                "pitch_type":            "FF",
                "recommended_pitch":     "SL",
                "followed_recommendation": False,
                "balls":   0,
                "strikes": 0,
            },
            {
                "pitcher_name":          "Chris Sale",
                "pitch_type":            "SL",
                "recommended_pitch":     "SL",
                "followed_recommendation": True,
                "balls":   0,
                "strikes": 2,
            },
        ])

        print("Mock DataStore ready")

    def get_pitcher_names(self) -> list[str]:
        """Return a sorted list of all pitcher names in the dataset.

        Returns:
            Alphabetically sorted list of pitcher name strings.
        """
        return sorted(self.pitcher_profiles["pitcher_name"].tolist())

    def get_pitcher_profile(self, name: str) -> dict | None:
        """Return the profile dict for a single pitcher by exact name match.

        Args:
            name: Pitcher's full name, case-sensitive.

        Returns:
            Dict of profile fields, or None if the pitcher is not found.
        """
        result = self.pitcher_profiles[
            self.pitcher_profiles["pitcher_name"] == name
        ]
        return result.iloc[0].to_dict() if len(result) > 0 else None


# Single global instance — loaded once when the module is first imported
store = DataStore()