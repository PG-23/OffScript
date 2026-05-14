# api/routers/pitchers.py

from fastapi import APIRouter, HTTPException
from api.config import store
from api.models.schemas import PitcherProfile, PitcherSummary
import numpy as np

router = APIRouter()

@router.get("/", response_model=list[PitcherSummary])
def get_all_pitchers():
    """Return all pitcher profiles sorted by deviation score."""
    profiles = store.pitcher_profiles.sort_values(
        'deviation_score', ascending=False
    )
    return [
        PitcherSummary(
            pitcher_name=row['pitcher_name'],
            deviation_score=round(float(row['deviation_score']), 2),
            deviation_advantage=round(float(row['deviation_advantage']), 2)
        )
        for _, row in profiles.iterrows()
    ]

@router.get("/{pitcher_name}", response_model=PitcherProfile)
def get_pitcher_profile(pitcher_name: str):
    """Return full deviation profile for a specific pitcher."""
    profiles = store.pitcher_profiles
    match = profiles[
        profiles['pitcher_name'].str.lower() == pitcher_name.lower()
    ]

    if len(match) == 0:
        available = store.get_pitcher_names()
        raise HTTPException(
            status_code=404,
            detail=f"Pitcher '{pitcher_name}' not found. "
                   f"Available: {available}"
        )

    row = match.iloc[0]

    # Print row contents to terminal for debugging
    print("DEBUG row contents:")
    print(row.to_dict())
    print("DEBUG dtypes:")
    print(row.index.tolist())

    try:
        return PitcherProfile(
            pitcher_name=str(row['pitcher_name']),
            total_pitches=int(row['total_pitches']),
            deviation_score=round(float(row['deviation_score']), 2),
            deviation_advantage=round(float(row['deviation_advantage']), 2),
            two_strike_dev_cost=round(float(row['two_strike_dev_cost']), 2),
            arsenal_size=int(row['arsenal_size']),
            deviation_rank=int(row['deviation_rank']) 
                           if 'deviation_rank' in row.index 
                           else 0
        )
    except Exception as e:
        print(f"ERROR building response: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error building pitcher profile: {str(e)}"
        )

@router.get("/{pitcher_name}/arsenal")
def get_pitcher_arsenal(pitcher_name: str):
    """Return pitch type distribution for a specific pitcher."""
    data = store.pitcher_data
    match = data[
        data['pitcher_name'].str.lower() == pitcher_name.lower()
    ]

    if len(match) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Pitcher '{pitcher_name}' not found."
        )

    arsenal = (match['pitch_type']
               .value_counts(normalize=True)
               .round(3)
               .to_dict())

    return {
        "pitcher_name": match.iloc[0]['pitcher_name'],
        "total_pitches": len(match),
        "arsenal": arsenal
    }

@router.get("/{pitcher_name}/deviations")
def get_pitcher_deviations(pitcher_name: str):
    """Return deviation substitution patterns for a pitcher."""
    data = store.pitcher_data
    match = data[
        data['pitcher_name'].str.lower() == pitcher_name.lower()
    ]

    if len(match) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Pitcher '{pitcher_name}' not found."
        )

    deviations = match[~match['followed_recommendation']].copy()

    substitutions = (
        deviations.groupby(['recommended_pitch', 'pitch_type'])
        .size()
        .reset_index(name='count')
    )
    substitutions['pct'] = (
        substitutions.groupby('recommended_pitch')['count']
        .transform(lambda x: (x / x.sum() * 100).round(1))
    )

    result = {}
    for rec_pitch in substitutions['recommended_pitch'].unique():
        subset = substitutions[
            substitutions['recommended_pitch'] == rec_pitch
        ].sort_values('count', ascending=False)
        result[rec_pitch] = [
            {
                "thrown": row['pitch_type'],
                "count": int(row['count']),
                "pct": float(row['pct'])
            }
            for _, row in subset.iterrows()
        ]

    return {
        "pitcher_name": match.iloc[0]['pitcher_name'],
        "total_deviations": len(deviations),
        "deviation_rate": round(
            len(deviations) / len(match) * 100, 1
        ),
        "substitution_patterns": result
    }

@router.get("/debug/columns")
def debug_columns():
    """Temporary diagnostic endpoint."""
    return {
        "columns": store.pitcher_profiles.columns.tolist(),
        "dtypes": store.pitcher_profiles.dtypes.astype(str).to_dict(),
        "sample": store.pitcher_profiles.iloc[0].to_dict()
    }