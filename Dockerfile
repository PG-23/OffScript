# OffScript API — Dockerfile
#
# Build strategy:
#   - python:3.11-slim keeps the image small
#   - requirements are copied and installed before application code so
#     Docker layer caching skips the pip install step on code-only changes
#   - Small encoder files are baked in from the repo (< 1 KB each)
#   - The main model (~8 MB) is downloaded at build time via startup.py
#     rather than committed to the repo, keeping repository size manageable

FROM python:3.11-slim

# ── Environment ────────────────────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# ── System dependencies ────────────────────────────────────────────────────
# gcc and g++ are required by some Python packages (e.g. xgboost, shap).
# The apt cache is cleared in the same layer to keep image size minimal.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ────────────────────────────────────────────────────
# Copied before application code so this layer is only invalidated when
# requirements-api.txt changes, not on every code change.
COPY requirements-api.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements-api.txt

# ── Application code ───────────────────────────────────────────────────────
COPY api/ ./api/
COPY src/ ./src/

# ── Data and model artifacts ───────────────────────────────────────────────
# Deploy data subset: small parquet files committed to the repo and baked
# into the image. Avoids the need for external volumes or cloud storage.
COPY data/deploy/ ./data/deploy/

# Encoder files: committed to the repo because they are tiny (< 1 KB each).
# The main model file is downloaded separately by startup.py below.
COPY models/label_encoder.pkl ./models/
COPY models/pitcher_encoder.pkl ./models/

# Runtime directories used by the application
RUN mkdir -p data/processed models

# ── Model download ─────────────────────────────────────────────────────────
# Downloads the baseline pitch model (~8 MB) from GitHub Releases at build
# time. Running this once during the build rather than at container startup
# keeps startup time fast and makes the model available immediately.
RUN python api/startup.py

# ── Runtime ────────────────────────────────────────────────────────────────
EXPOSE 8000

# Health check: Docker monitors this endpoint to determine container health.
# start-period gives the API time to fully initialize before checks begin.
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" \
    || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]