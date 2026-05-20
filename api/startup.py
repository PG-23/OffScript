# api/startup.py
"""Model availability check and download utility.

Ensures the baseline pitch model is present on disk before the API starts.
The model is stored in GitHub Releases rather than the repository to keep
repo size small. This module is called from both api/main.py at startup
and from the Dockerfile RUN step at build time.
"""

import os
import urllib.request
from pathlib import Path

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "baseline_pitch_model.pkl"

MODEL_URL = (
    "https://github.com/PG-23/OffScript/releases/download/v1.0.0/"
    "baseline_pitch_model.pkl"
)


def ensure_model_exists() -> None:
    """Download the baseline pitch model if not already present locally.

    Checks for the model at MODEL_PATH. If found, returns immediately.
    If not found, downloads from GitHub Releases and saves to MODEL_PATH.
    Raises RuntimeError if the download fails so startup is aborted rather
    than silently serving a broken API.

    Raises:
        RuntimeError: If the model cannot be downloaded from MODEL_URL.
    """
    if MODEL_PATH.exists():
        print(f"Model found: {MODEL_PATH}")
        return

    print("Model not found — downloading from GitHub Releases...")
    os.makedirs(MODEL_PATH.parent, exist_ok=True)

    try:
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        size_mb = MODEL_PATH.stat().st_size / 1024 / 1024
        print(f"Model downloaded successfully ({size_mb:.1f} MB)")
    except Exception as e:
        raise RuntimeError(
            f"Could not download model from {MODEL_URL}. "
            f"Check the URL and your internet connection. "
            f"Original error: {e}"
        ) from e


if __name__ == "__main__":
    ensure_model_exists()