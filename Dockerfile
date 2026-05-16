# Dockerfile

# Use official Python slim image for smaller container size
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies needed by some Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first — Docker layer caching means this
# layer only rebuilds when requirements change, not on every
# code change. This significantly speeds up rebuilds.
COPY requirements-api.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-api.txt

# Copy application code
COPY api/ ./api/
COPY src/ ./src/

# Copy the minimal deploy data subset — these small parquet files
# are committed to the repository and baked directly into the image.
# This avoids the need for external volumes or cloud storage for
# the analytical data the API serves.
COPY data/deploy/ ./data/deploy/

# Copy the small encoder files — these are committed to the repo
# because they are tiny (< 1 KB each). The main model file is
# downloaded separately at build time via startup.py.
COPY models/label_encoder.pkl ./models/
COPY models/pitcher_encoder.pkl ./models/

# Create directories for data and models
# data/processed is used locally but not in deployment
# models/ holds the downloaded model file after startup.py runs
RUN mkdir -p data/processed models

# Download the baseline pitch model from GitHub Releases at build time.
# This runs once during the image build rather than at every container
# startup, keeping startup time fast. The model is ~8 MB and is stored
# in GitHub Releases rather than the repository to keep repo size small.
RUN python api/startup.py

# Expose the port the API runs on
EXPOSE 8000

# Health check — Docker will monitor this to know if container is healthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" \
    || exit 1

# Start the API
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]