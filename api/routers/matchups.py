# api/routers/matchups.py
"""Matchup analysis endpoints.

Exposes pitcher-batter exploitation scores derived from the Phase 4
matchup engine. Scores reflect how well a batter is positioned to
exploit a pitcher's deviation tendencies.
"""

from fastapi import APIRouter, HTTPException, Query

from api.config import store
from api.models.schemas import MatchupList, MatchupScore

router = APIRouter()

# Exploitation tier thresholds — mirrors the scoring scale defined in
# notebook 08 where scores are weighted matchup percentages (0–100).
_TIER_THRESHOLDS = [
    (55, "Elite Exploitation"),
    (45, "High Exploitation"),
    (35, "Moderate Exploitation"),
]


def get_exploitation_tier(score: float) -> str:
    """Classify a matchup score into a human-readable exploitation tier.

    Args:
        score: Matchup exploitation score (0–100).

    Returns:
        One of 'Elite Exploitation', 'High Exploitation',
        'Moderate Exploitation', or 'Low Exploitation'.
    """
    for threshold, label in _TIER_THRESHOLDS:
        if score >= threshold:
            return label
    return "Low Exploitation"


def _resolve_pitcher(pitcher_name: str) -> "pd.DataFrame":
    """Filter matchup data to a single pitcher with case-insensitive match.

    Args:
        pitcher_name: Pitcher name from the URL path parameter.

    Returns:
        Filtered DataFrame rows for the matched pitcher.

    Raises:
        HTTPException: 404 if no rows match the pitcher name.
    """
    matchups = store.matchup_scores
    match = matchups[matchups["pitcher_name"].str.lower() == pitcher_name.lower()]
    if len(match) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No matchup data found for '{pitcher_name}'.",
        )
    return match


@router.get("/{pitcher_name}", response_model=MatchupList)
def get_pitcher_matchups(
    pitcher_name: str,
    top_n: int = Query(10, ge=1, le=50, description="Number of matchups to return"),
    stand: str | None = Query(None, description="Filter by batter handedness: L or R"),
) -> MatchupList:
    """Return the batters most likely to exploit a pitcher's deviation patterns.

    Results are ranked by matchup score descending. Optionally filtered
    by batter handedness.

    Args:
        pitcher_name: Pitcher's full name (case-insensitive).
        top_n: Maximum number of matchups to return (1–50, default 10).
        stand: Optional handedness filter — 'L' for left, 'R' for right.

    Returns:
        MatchupList containing ranked matchup scores and total count.

    Raises:
        HTTPException: 404 if pitcher not found, 400 if stand is invalid.
    """
    match = _resolve_pitcher(pitcher_name)

    if stand:
        if stand.upper() not in ("L", "R"):
            raise HTTPException(
                status_code=400,
                detail="stand must be 'L' or 'R'.",
            )
        match = match[match["stand"] == stand.upper()]

    top = match.sort_values("matchup_score", ascending=False).head(top_n)

    matchup_list = [
        MatchupScore(
            pitcher_name=str(row["pitcher_name"]),
            batter_name=str(row["batter_name"]),
            batter_id=int(row["batter_id"]),
            stand=str(row["stand"]),
            matchup_score=round(float(row["matchup_score"]), 2),
            exploitation_tier=get_exploitation_tier(float(row["matchup_score"])),
        )
        for _, row in top.iterrows()
    ]

    return MatchupList(
        pitcher_name=match.iloc[0]["pitcher_name"],
        matchups=matchup_list,
        total_matchups=len(match),
    )


@router.get("/{pitcher_name}/{batter_name}")
def get_specific_matchup(pitcher_name: str, batter_name: str) -> dict:
    """Return matchup score for a specific pitcher-batter combination.

    Returns scores for both handedness splits if the batter appears
    in both left and right-handed matchup data.

    Args:
        pitcher_name: Pitcher's full name (case-insensitive).
        batter_name: Batter's full name (case-insensitive).

    Returns:
        Dict containing pitcher name, batter name, and a list of
        matchup records (one per handedness split present in data).

    Raises:
        HTTPException: 404 if the pitcher-batter combination is not found.
    """
    matchups = store.matchup_scores
    match = matchups[
        (matchups["pitcher_name"].str.lower() == pitcher_name.lower())
        & (matchups["batter_name"].str.lower() == batter_name.lower())
    ]

    if len(match) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No matchup data found for '{pitcher_name}' vs '{batter_name}'.",
        )

    results = [
        {
            "pitcher_name": row["pitcher_name"],
            "batter_name": row["batter_name"],
            "stand": row["stand"],
            "matchup_score": round(float(row["matchup_score"]), 2),
            "exploitation_tier": get_exploitation_tier(float(row["matchup_score"])),
        }
        for _, row in match.iterrows()
    ]

    return {
        "pitcher_name": match.iloc[0]["pitcher_name"],
        "batter_name": match.iloc[0]["batter_name"],
        "matchups": results,
    }