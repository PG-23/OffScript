# api/main.py
"""FastAPI application entry point for the OffScript API.

Initializes the application, registers middleware and routers, and
exposes root and health check endpoints. The baseline pitch model is
downloaded via startup.py before the application starts if not already
present in the models/ directory.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from api.config import store
from api.models.schemas import HealthCheck
from api.routers import matchups, pitchers, recommend
from api.startup import ensure_model_exists

# Download model from GitHub Releases if not already present
ensure_model_exists()

# ── Application ───────────────────────────────────────────────────────────

app = FastAPI(
    title="OffScript API",
    description=(
        "MLB pitch selection theory and deviation analysis API. "
        "Derives optimal pitch recommendations from Statcast data "
        "and identifies pitcher deviation patterns."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware ────────────────────────────────────────────────────────────

# CORS: open wildcard suitable for a public portfolio API. Restrict
# allow_origins to specific domains before any production deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus: instruments all routes automatically and exposes a /metrics
# endpoint that Prometheus scrapes on a 15-second interval. Metrics include
# request counts, latency histograms, and in-flight request gauges per
# endpoint and HTTP method.
Instrumentator().instrument(app).expose(app)

# ── Routers ───────────────────────────────────────────────────────────────

app.include_router(pitchers.router, prefix="/pitchers", tags=["Pitchers"])
app.include_router(matchups.router, prefix="/matchups", tags=["Matchups"])
app.include_router(recommend.router, prefix="/recommend", tags=["Recommend"])

# ── Endpoints ─────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
def root() -> dict:
    """Redirect hint for API root — points consumers to /docs."""
    return {
        "message": "OffScript API",
        "docs": "/docs",
        "version": "1.0.0",
    }


@app.get("/health", response_model=HealthCheck, tags=["Health"])
def health_check() -> HealthCheck:
    """Return API health status including model and data load state.

    Used by the Docker HEALTHCHECK and any uptime monitoring. Returns
    a 200 with a HealthCheck payload when the API is fully operational.
    """
    return HealthCheck(
        status="healthy",
        pitchers_loaded=len(store.get_pitcher_names()),
        model_loaded=store.model is not None,
        version="1.0.0",
    )