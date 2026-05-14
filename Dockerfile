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

# Create directories for data and models
# These will be populated via Docker volumes at runtime
RUN mkdir -p data/processed models

# Expose the port the API runs on
EXPOSE 8000

# Health check — Docker will monitor this to know if container is healthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" \
    || exit 1

# Start the API
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]