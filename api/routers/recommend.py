# api/routers/recommend.py

from fastapi import APIRouter, HTTPException
from api.config import store
from api.models.schemas import PitchRecommendRequest, PitchRecommendation
import numpy as np
import pandas as pd

router = APIRouter()

FEATURE_COLS = [
    'balls', 'strikes', 'inning', 'score_diff',
    'on_1b', 'on_2b', 'on_3b',
    'runners_on', 'scoring_position',
    'stand_encoded', 'pitcher_encoded', 'count_leverage'
]

@router.post("/", response_model=PitchRecommendation)
def recommend_pitch(request: PitchRecommendRequest):
    """
    Given a game situation and pitcher, return the model's
    recommended pitch type with confidence scores.
    """
    # Validate pitcher exists in encoder
    known_pitchers = list(store.pitcher_encoder.classes_)
    pitcher_match = [p for p in known_pitchers
                     if p.lower() == request.pitcher_name.lower()]

    if not pitcher_match:
        raise HTTPException(
            status_code=404,
            detail=f"Pitcher '{request.pitcher_name}' not found. "
                   f"Known pitchers: {known_pitchers}"
        )

    pitcher_name = pitcher_match[0]
    pitcher_encoded = store.pitcher_encoder.transform(
        [pitcher_name]
    )[0]

    # Engineer features to match training
    runners_on = request.on_1b + request.on_2b + request.on_3b
    scoring_position = int(request.on_2b > 0 or request.on_3b > 0)
    stand_encoded = int(request.batter_hand == 'R')
    count_leverage = (
        int(request.strikes == 2) * 2 +
        int(request.balls == 3) * 2 +
        int(request.strikes == 1) +
        int(request.balls == 2)
    )

    features = pd.DataFrame([{
        'balls': request.balls,
        'strikes': request.strikes,
        'inning': request.inning,
        'score_diff': request.score_diff,
        'on_1b': request.on_1b,
        'on_2b': request.on_2b,
        'on_3b': request.on_3b,
        'runners_on': runners_on,
        'scoring_position': scoring_position,
        'stand_encoded': stand_encoded,
        'pitcher_encoded': int(pitcher_encoded),
        'count_leverage': count_leverage
    }])[FEATURE_COLS]

    # Generate prediction
    proba = store.model.predict_proba(features)[0]
    classes = store.label_encoder.classes_
    recommended_idx = np.argmax(proba)
    recommended_pitch = classes[recommended_idx]
    confidence = round(float(proba[recommended_idx]), 3)

    # Build probability dictionary
    probabilities = {
        cls: round(float(p), 3)
        for cls, p in zip(classes, proba)
    }

    # Build human readable situation summary
    runners = []
    if request.on_1b:
        runners.append("1st")
    if request.on_2b:
        runners.append("2nd")
    if request.on_3b:
        runners.append("3rd")

    runner_str = (", ".join(runners) if runners else "bases empty")
    situation_summary = (
        f"{request.balls}-{request.strikes} count, "
        f"inning {request.inning}, "
        f"{runner_str}, "
        f"score diff {request.score_diff:+d}, "
        f"batter bats {request.batter_hand}"
    )

    return PitchRecommendation(
        recommended_pitch=recommended_pitch,
        confidence=confidence,
        probabilities=probabilities,
        situation_summary=situation_summary
    )