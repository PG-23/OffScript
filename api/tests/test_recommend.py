# api/tests/test_recommend.py

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

# Base valid payload reused across tests
_BASE_PAYLOAD = {
    "pitcher_name": "Gerrit Cole",
    "balls": 0,
    "strikes": 2,
    "inning": 7,
    "score_diff": 0,
    "on_1b": 0,
    "on_2b": 0,
    "on_3b": 0,
    "batter_hand": "R",
}


def _payload(**overrides) -> dict:
    """Return a copy of the base payload with specified fields overridden."""
    return {**_BASE_PAYLOAD, **overrides}


# ── Valid requests ────────────────────────────────────────────────────────

def test_valid_recommendation():
    """Valid request returns 200 with all required response fields."""
    response = client.post("/recommend/", json=_BASE_PAYLOAD)
    assert response.status_code == 200
    data = response.json()
    assert "recommended_pitch" in data
    assert "confidence" in data
    assert "probabilities" in data
    assert "situation_summary" in data


def test_recommendation_confidence_range():
    """Confidence score is a valid probability between 0 and 1."""
    response = client.post("/recommend/", json=_BASE_PAYLOAD)
    assert response.status_code == 200
    assert 0 < response.json()["confidence"] < 1


def test_recommendation_probabilities_sum():
    """Probability distribution across all pitch types sums to ~1.0."""
    response = client.post("/recommend/", json=_BASE_PAYLOAD)
    assert response.status_code == 200
    total = sum(response.json()["probabilities"].values())
    assert 0.99 <= total <= 1.01


def test_recommendation_situation_summary_present():
    """Situation summary string is non-empty."""
    response = client.post("/recommend/", json=_BASE_PAYLOAD)
    assert response.status_code == 200
    assert len(response.json()["situation_summary"]) > 0


def test_recommendation_left_handed_batter():
    """Request with left-handed batter returns a valid recommendation."""
    response = client.post("/recommend/", json=_payload(batter_hand="L"))
    assert response.status_code == 200
    assert "recommended_pitch" in response.json()


def test_recommendation_bases_loaded():
    """Request with bases loaded returns a valid recommendation."""
    response = client.post("/recommend/", json=_payload(on_1b=1, on_2b=1, on_3b=1))
    assert response.status_code == 200
    assert "recommended_pitch" in response.json()


# ── Invalid pitcher ───────────────────────────────────────────────────────

def test_invalid_pitcher_recommendation():
    """Unknown pitcher name returns 404."""
    response = client.post("/recommend/", json=_payload(pitcher_name="Fake Player"))
    assert response.status_code == 404


# ── Input validation (422 Unprocessable Entity) ───────────────────────────

@pytest.mark.parametrize("balls", [-1, 4, 5])
def test_invalid_ball_count(balls):
    """Ball count outside 0–3 returns 422."""
    response = client.post("/recommend/", json=_payload(balls=balls))
    assert response.status_code == 422


@pytest.mark.parametrize("strikes", [-1, 3, 4])
def test_invalid_strike_count(strikes):
    """Strike count outside 0–2 returns 422."""
    response = client.post("/recommend/", json=_payload(strikes=strikes))
    assert response.status_code == 422


@pytest.mark.parametrize("inning", [0, -1, 11])
def test_invalid_inning(inning):
    """Inning outside 1–10 returns 422."""
    response = client.post("/recommend/", json=_payload(inning=inning))
    assert response.status_code == 422


def test_invalid_batter_hand():
    """Batter hand value other than L or R returns 422."""
    response = client.post("/recommend/", json=_payload(batter_hand="X"))
    assert response.status_code == 422


def test_missing_required_field():
    """Omitting a required field returns 422."""
    payload = {k: v for k, v in _BASE_PAYLOAD.items() if k != "pitcher_name"}
    response = client.post("/recommend/", json=payload)
    assert response.status_code == 422