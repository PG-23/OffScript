# api/routers/recommend.py
"""Pitch recommendation endpoint.

Accepts a game situation and pitcher name, engineers the feature vector
used during training, and returns the model's recommended pitch type with
full class probability scores.
"""

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException

from api.config import store
from api.models.schemas import PitchRecommendRequest, PitchRecommendation

router = APIRouter()

# Feature column order must exactly match the training order defined in
# notebook 05. XGBoost is sensitive to column ordering at inference time.
FEATURE_COLS = [
    "balls", "strikes", "inning", "score_diff",
    "on_1b", "on_2b", "on_3b",
    "runners_on", "scoring_position",
    "stand_encoded", "pitcher_encoded", "count_leverage",
]


@router.post("/", response_model=PitchRecommendation)
def recommend_pitch(request: PitchRecommendRequest) -> PitchRecommendation:
    """Return the model's recommended pitch type for a given game situation.

    Engineers the same feature vector used during model training from the
    incoming request, runs inference, and returns the top recommendation
    with full class probabilities and a human-readable situation summary.

    Args:
        request: PitchRecommendRequest containing pitcher name, count,
            baserunner state, inning, score differential, and batter hand.

    Returns:
        PitchRecommendation with recommended pitch type, confidence score,
        full probability distribution, and situation summary string.

    Raises:
        HTTPException: 404 if the pitcher name is not recognized by the
            label encoder loaded from the Phase 2 model artifacts.
    """
    # Resolve pitcher name case-insensitively against the encoder's classes
    known_pitchers = list(store.pitcher_encoder.classes_)
    pitcher_match = [p for p in known_pitchers if p.lower() == request.pitcher_name.lower()]

    if not pitcher_match:
        raise HTTPException(
            status_code=404,
            detail=f"Pitcher '{request.pitcher_name}' not found. "
                   f"Known pitchers: {known_pitchers}",
        )

    pitcher_name = pitcher_match[0]
    pitcher_encoded = int(store.pitcher_encoder.transform([pitcher_name])[0])

    # Engineer features — must mirror the logic in notebook 05 exactly
    runners_on       = request.on_1b + request.on_2b + request.on_3b
    scoring_position = int(request.on_2b > 0 or request.on_3b > 0)
    stand_encoded    = int(request.batter_hand == "R")
    count_leverage   = (
        int(request.strikes == 2) * 2
        + int(request.balls == 3) * 2
        + int(request.strikes == 1)
        + int(request.balls == 2)
    )

    features = pd.DataFrame([{
        "balls":            request.balls,
        "strikes":          request.strikes,
        "inning":           request.inning,
        "score_diff":       request.score_diff,
        "on_1b":            request.on_1b,
        "on_2b":            request.on_2b,
        "on_3b":            request.on_3b,
        "runners_on":       runners_on,
        "scoring_position": scoring_position,
        "stand_encoded":    stand_encoded,
        "pitcher_encoded":  pitcher_encoded,
        "count_leverage":   count_leverage,
    }])[FEATURE_COLS]

    # Run inference
    proba = store.model.predict_proba(features)[0]
    classes = store.label_encoder.classes_
    recommended_idx = int(np.argmax(proba))
    recommended_pitch = classes[recommended_idx]
    confidence = round(float(proba[recommended_idx]), 3)

    probabilities = {cls: round(float(p), 3) for cls, p in zip(classes, proba)}

    # Build human-readable situation summary
    runners = [
        base for base, occupied in [
            ("1st", request.on_1b),
            ("2nd", request.on_2b),
            ("3rd", request.on_3b),
        ]
        if occupied
    ]
    runner_str = ", ".join(runners) if runners else "bases empty"
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
        situation_summary=situation_summary,
    )