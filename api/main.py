# api/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.startup import ensure_model_exists
from api.routers import pitchers, matchups, recommend
from api.models.schemas import HealthCheck
from api.config import store

# Download model if not present — runs before app starts
ensure_model_exists()

app = FastAPI(
    title="OffScript API",
    description=(
        "MLB pitch selection theory and deviation analysis API. "
        "Derives optimal pitch recommendations from Statcast data "
        "and identifies pitcher deviation patterns."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware — allows future frontend/game to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(pitchers.router, prefix="/pitchers", tags=["Pitchers"])
app.include_router(matchups.router, prefix="/matchups", tags=["Matchups"])
app.include_router(recommend.router, prefix="/recommend", tags=["Recommend"])

@app.get("/", include_in_schema=False)
def root():
    return {
        "message": "OffScript API",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/health", response_model=HealthCheck, tags=["Health"])
def health_check():
    return HealthCheck(
        status="healthy",
        pitchers_loaded=len(store.get_pitcher_names()),
        model_loaded=store.model is not None,
        version="1.0.0"
    )