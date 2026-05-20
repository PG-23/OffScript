# api/routers/pitchers.py
"""Pitcher profile and analysis endpoints.

Exposes pitcher deviation profiles, pitch arsenals, and substitution
patterns derived from the Phase 2 and Phase 3 analysis notebooks.
"""

from fastapi import APIRouter, HTTPException

from api.config import store
from api.models.schemas import PitcherProfile, PitcherSummary

router = APIRouter()


def _resolve_pitcher_data(pitcher_name: str) -> "pd.DataFrame":
    """Filter pitch-level data to a single pitcher with case-insensitive match.

    Args:
        pitcher_name: Pitcher name from the URL path parameter.

    Returns:
        Filtered DataFrame rows for the matched pitcher.

    Raises:
        HTTPException: 404 if pitcher not found.
    """
    data = store.pitcher_data
    match = data[data["pitcher_name"].str.lower() == pitcher_name.lower()]
    if len(match) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Pitcher '{pitcher_name}' not found. "
                   f"Available: {store.get_pitcher_names()}",
        )
    return match


@router.get("/", response_model=list[PitcherSummary])
def get_all_pitchers() -> list[PitcherSummary]:
    """Return all pitcher profiles sorted by deviation score descending.

    Returns:
        List of PitcherSummary objects covering all 15 pitchers in
        the dataset, ordered from highest to lowest deviation score.
    """
    profiles = store.pitcher_profiles.sort_values("deviation_score", ascending=False)
    return [
        PitcherSummary(
            pitcher_name=row["pitcher_name"],
            deviation_score=round(float(row["deviation_score"]), 2),
            deviation_advantage=round(float(row["deviation_advantage"]), 2),
        )
        for _, row in profiles.iterrows()
    ]


@router.get("/{pitcher_name}/arsenal")
def get_pitcher_arsenal(pitcher_name: str) -> dict:
    """Return pitch type distribution for a specific pitcher.

    Args:
        pitcher_name: Pitcher's full name (case-insensitive).

    Returns:
        Dict containing pitcher name, total pitch count, and a mapping
        of pitch type codes to usage rates (0.0–1.0).

    Raises:
        HTTPException: 404 if pitcher not found.
    """
    match = _resolve_pitcher_data(pitcher_name)
    arsenal = match["pitch_type"].value_counts(normalize=True).round(3).to_dict()

    return {
        "pitcher_name": match.iloc[0]["pitcher_name"],
        "total_pitches": len(match),
        "arsenal": arsenal,
    }


@router.get("/{pitcher_name}/deviations")
def get_pitcher_deviations(pitcher_name: str) -> dict:
    """Return deviation substitution patterns for a pitcher.

    For each pitch type the model recommended, shows what the pitcher
    actually threw instead and how frequently. Only deviating pitches
    are included — pitches where the pitcher followed the recommendation
    are excluded.

    Args:
        pitcher_name: Pitcher's full name (case-insensitive).

    Returns:
        Dict containing pitcher name, total deviation count, deviation
        rate percentage, and substitution patterns keyed by recommended
        pitch type.

    Raises:
        HTTPException: 404 if pitcher not found.
    """
    match = _resolve_pitcher_data(pitcher_name)
    deviations = match[~match["followed_recommendation"]].copy()

    substitutions = (
        deviations.groupby(["recommended_pitch", "pitch_type"])
        .size()
        .reset_index(name="count")
    )
    substitutions["pct"] = substitutions.groupby("recommended_pitch")["count"].transform(
        lambda x: (x / x.sum() * 100).round(1)
    )

    result = {
        rec_pitch: [
            {
                "thrown": row["pitch_type"],
                "count": int(row["count"]),
                "pct": float(row["pct"]),
            }
            for _, row in substitutions[
                substitutions["recommended_pitch"] == rec_pitch
            ].sort_values("count", ascending=False).iterrows()
        ]
        for rec_pitch in substitutions["recommended_pitch"].unique()
    }

    return {
        "pitcher_name": match.iloc[0]["pitcher_name"],
        "total_deviations": len(deviations),
        "deviation_rate": round(len(deviations) / len(match) * 100, 1),
        "substitution_patterns": result,
    }


@router.get("/{pitcher_name}", response_model=PitcherProfile)
def get_pitcher_profile(pitcher_name: str) -> PitcherProfile:
    """Return the full deviation profile for a specific pitcher.

    Args:
        pitcher_name: Pitcher's full name (case-insensitive).

    Returns:
        PitcherProfile containing deviation score, advantage, two-strike
        cost, arsenal size, and deviation rank.

    Raises:
        HTTPException: 404 if pitcher not found, 500 if profile
            construction fails unexpectedly.
    """
    profiles = store.pitcher_profiles
    match = profiles[profiles["pitcher_name"].str.lower() == pitcher_name.lower()]

    if len(match) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Pitcher '{pitcher_name}' not found. "
                   f"Available: {store.get_pitcher_names()}",
        )

    row = match.iloc[0]

    try:
        return PitcherProfile(
            pitcher_name=str(row["pitcher_name"]),
            total_pitches=int(row["total_pitches"]),
            deviation_score=round(float(row["deviation_score"]), 2),
            deviation_advantage=round(float(row["deviation_advantage"]), 2),
            two_strike_dev_cost=round(float(row["two_strike_dev_cost"]), 2),
            arsenal_size=int(row["arsenal_size"]),
            deviation_rank=int(row["deviation_rank"])
            if "deviation_rank" in row.index
            else 0,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error building pitcher profile: {e}",
        ) from e