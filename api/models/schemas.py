# api/models/schemas.py

from pydantic import BaseModel, Field
from typing import Optional

# ── Request Schemas ──────────────────────────────────────────

class PitchRecommendRequest(BaseModel):
    pitcher_name: str = Field(
        ..., 
        description="Full pitcher name e.g. 'Gerrit Cole'"
    )
    balls: int = Field(..., ge=0, le=3, description="Current ball count")
    strikes: int = Field(..., ge=0, le=2, description="Current strike count")
    inning: int = Field(..., ge=1, le=10, description="Current inning")
    score_diff: int = Field(
        ..., ge=-20, le=20,
        description="Score differential (home - away)"
    )
    on_1b: int = Field(0, ge=0, le=1, description="Runner on first (0/1)")
    on_2b: int = Field(0, ge=0, le=1, description="Runner on second (0/1)")
    on_3b: int = Field(0, ge=0, le=1, description="Runner on third (0/1)")
    batter_hand: str = Field(
        ..., description="Batter handedness: 'L' or 'R'"
    )

# ── Response Schemas ─────────────────────────────────────────

class PitchRecommendation(BaseModel):
    recommended_pitch: str
    confidence: float
    probabilities: dict[str, float]
    situation_summary: str

class PitcherProfile(BaseModel):
    pitcher_name: str
    total_pitches: int
    deviation_score: float
    deviation_advantage: float
    two_strike_dev_cost: float
    arsenal_size: int
    deviation_rank: int

class PitcherSummary(BaseModel):
    pitcher_name: str
    deviation_score: float
    deviation_advantage: float

class MatchupScore(BaseModel):
    pitcher_name: str
    batter_name: str
    batter_id: int
    stand: str
    matchup_score: float
    exploitation_tier: str

class MatchupList(BaseModel):
    pitcher_name: str
    matchups: list[MatchupScore]
    total_matchups: int

class HealthCheck(BaseModel):
    status: str
    pitchers_loaded: int
    model_loaded: bool
    version: str