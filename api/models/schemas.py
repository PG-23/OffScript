# api/models/schemas.py
"""Pydantic request and response schemas for the OffScript API.

All schemas are used by FastAPI for automatic request validation,
response serialization, and OpenAPI documentation generation.
"""

from pydantic import BaseModel, Field, field_validator


# ── Request schemas ───────────────────────────────────────────────────────

class PitchRecommendRequest(BaseModel):
    """Request body for the POST /recommend/ endpoint.

    Represents the full game situation at the time of a pitch. All count
    and baserunner fields are validated against legal baseball values.
    """

    pitcher_name: str = Field(
        ...,
        description="Pitcher's full name, e.g. 'Gerrit Cole'",
        examples=["Gerrit Cole"],
    )
    balls: int = Field(
        ..., ge=0, le=3,
        description="Current ball count (0–3)",
    )
    strikes: int = Field(
        ..., ge=0, le=2,
        description="Current strike count (0–2)",
    )
    inning: int = Field(
        ..., ge=1, le=10,
        description="Current inning (1–10)",
    )
    score_diff: int = Field(
        ..., ge=-20, le=20,
        description="Score differential at time of pitch (home minus away)",
    )
    on_1b: int = Field(0, ge=0, le=1, description="Runner on first base (0 or 1)")
    on_2b: int = Field(0, ge=0, le=1, description="Runner on second base (0 or 1)")
    on_3b: int = Field(0, ge=0, le=1, description="Runner on third base (0 or 1)")
    batter_hand: str = Field(
        ...,
        description="Batter handedness: 'L' for left, 'R' for right",
        examples=["R"],
    )

    @field_validator("batter_hand")
    @classmethod
    def validate_batter_hand(cls, v: str) -> str:
        """Ensure batter_hand is 'L' or 'R'."""
        if v.upper() not in ("L", "R"):
            raise ValueError("batter_hand must be 'L' or 'R'")
        return v.upper()


# ── Response schemas ──────────────────────────────────────────────────────

class PitchRecommendation(BaseModel):
    """Response body for the POST /recommend/ endpoint."""

    recommended_pitch: str = Field(description="Statcast pitch type code, e.g. 'FF'")
    confidence: float = Field(description="Model probability for the recommended pitch (0–1)")
    probabilities: dict[str, float] = Field(
        description="Full probability distribution across all pitch types"
    )
    situation_summary: str = Field(description="Human-readable game situation string")


class PitcherProfile(BaseModel):
    """Full deviation profile for a single pitcher."""

    pitcher_name: str
    total_pitches: int
    deviation_score: float = Field(description="Deviation score 0–100; higher = deviates more")
    deviation_advantage: float = Field(
        description="Outcome advantage when deviating vs following model (% points)"
    )
    two_strike_dev_cost: float = Field(
        description="Deviation advantage specifically in two-strike counts"
    )
    arsenal_size: int = Field(description="Number of distinct pitch types thrown")
    deviation_rank: int = Field(description="Rank among all pitchers by deviation score")


class PitcherSummary(BaseModel):
    """Lightweight pitcher summary used in the GET /pitchers/ list."""

    pitcher_name: str
    deviation_score: float
    deviation_advantage: float


class MatchupScore(BaseModel):
    """Exploitation score for a single pitcher-batter combination."""

    pitcher_name: str
    batter_name: str
    batter_id: int
    stand: str = Field(description="Batter handedness: 'L' or 'R'")
    matchup_score: float = Field(description="Exploitation score 0–100; higher = more exploitable")
    exploitation_tier: str = Field(
        description="Human-readable tier: Elite / High / Moderate / Low Exploitation"
    )


class MatchupList(BaseModel):
    """Ranked list of matchup scores for a single pitcher."""

    pitcher_name: str
    matchups: list[MatchupScore]
    total_matchups: int = Field(description="Total matchups available before top_n filtering")


class HealthCheck(BaseModel):
    """Response body for the GET /health endpoint."""

    status: str = Field(description="'healthy' when the API is fully operational")
    pitchers_loaded: int = Field(description="Number of pitcher profiles loaded into memory")
    model_loaded: bool = Field(description="True if the XGBoost model is loaded")
    version: str