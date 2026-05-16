# api/startup.py

import os
import urllib.request
from pathlib import Path

MODEL_PATH = Path(__file__).resolve().parent.parent / 'models' / 'baseline_pitch_model.pkl'

MODEL_URL = (
    "https://github.com/PG-23/OffScript/releases/download/v1.0.0/"
    "baseline_pitch_model.pkl"
)

def ensure_model_exists():
    """Download model from GitHub Releases if not present locally."""
    if MODEL_PATH.exists():
        print(f"Model found at {MODEL_PATH}")
        return

    print(f"Model not found — downloading from GitHub Releases...")
    os.makedirs(MODEL_PATH.parent, exist_ok=True)

    try:
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        size_mb = MODEL_PATH.stat().st_size / 1024 / 1024
        print(f"Model downloaded successfully ({size_mb:.1f} MB)")
    except Exception as e:
        print(f"ERROR downloading model: {e}")
        raise RuntimeError(
            f"Could not download model from {MODEL_URL}. "
            f"Please check the URL and your internet connection."
        )

if __name__ == "__main__":
    ensure_model_exists()