# api/routers/matchups.py

from fastapi import APIRouter, HTTPException, Query
from api.config import store
from api.models.schemas import MatchupScore, MatchupList
from urllib.parse import unquote

router = APIRouter()

def get_exploitation_tier(score: float) -> str:
    """Classify matchup score into human readable tier."""
    if score >= 55:
        return "Elite Exploitation"
    elif score >= 45:
        return "High Exploitation"
    elif score >= 35:
        return "Moderate Exploitation"
    else:
        return "Low Exploitation"

@router.get("/{pitcher_name}", response_model=MatchupList)
def get_pitcher_matchups(
    
    pitcher_name: str,
    top_n: int = Query(10, ge=1, le=50,
                       description="Number of matchups to return"),
    stand: str = Query(None, description="Filter by batter hand: L or R")
):
    """
    Return the batters most likely to exploit a pitcher's
    deviation patterns, ranked by matchup score.
    """
    # Decode URL encoding e.g. Gerrit%20Cole -> Gerrit Cole
    pitcher_name = unquote(pitcher_name).strip()

    matchups = store.matchup_scores

    # Case insensitive pitcher match
    match = matchups[
        matchups['pitcher_name'].str.lower() == pitcher_name.lower()
    ]

    if len(match) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No matchup data found for '{pitcher_name}'."
        )

    # Optional handedness filter
    if stand:
        if stand.upper() not in ['L', 'R']:
            raise HTTPException(
                status_code=400,
                detail="stand must be 'L' or 'R'"
            )
        match = match[match['stand'] == stand.upper()]

    top = match.sort_values(
        'matchup_score', ascending=False
    ).head(top_n)

    matchup_list = [
        MatchupScore(
            pitcher_name=str(row['pitcher_name']),
            batter_name=str(row['batter_name']),
            batter_id=int(row['batter_id']),
            stand=str(row['stand']),
            matchup_score=round(float(row['matchup_score']), 2),
            exploitation_tier=get_exploitation_tier(
                float(row['matchup_score'])
            )
        )
        for _, row in top.iterrows()
    ]

    return MatchupList(
        pitcher_name=match.iloc[0]['pitcher_name'],
        matchups=matchup_list,
        total_matchups=len(match)
    )

@router.get("/{pitcher_name}/{batter_name}")
def get_specific_matchup(pitcher_name: str, batter_name: str):
    """Return matchup score for a specific pitcher-batter combination."""
    # Decode URL encoding e.g. Gerrit%20Cole -> Gerrit Cole
    pitcher_name = unquote(pitcher_name).strip()

    matchups = store.matchup_scores

    match = matchups[
        (matchups['pitcher_name'].str.lower() == pitcher_name.lower()) &
        (matchups['batter_name'].str.lower() == batter_name.lower())
    ]

    if len(match) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No matchup data found for "
                   f"'{pitcher_name}' vs '{batter_name}'."
        )

    results = []
    for _, row in match.iterrows():
        results.append({
            "pitcher_name": row['pitcher_name'],
            "batter_name": row['batter_name'],
            "stand": row['stand'],
            "matchup_score": round(float(row['matchup_score']), 2),
            "exploitation_tier": get_exploitation_tier(
                float(row['matchup_score'])
            )
        })

    return {
        "pitcher_name": match.iloc[0]['pitcher_name'],
        "batter_name": match.iloc[0]['batter_name'],
        "matchups": results
    }