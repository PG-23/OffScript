# api/tests/test_recommend.py

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_valid_recommendation():
    payload = {
        "pitcher_name": "Gerrit Cole",
        "balls": 0,
        "strikes": 2,
        "inning": 7,
        "score_diff": 0,
        "on_1b": 0,
        "on_2b": 0,
        "on_3b": 0,
        "batter_hand": "R"
    }
    response = client.post("/recommend/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "recommended_pitch" in data
    assert "confidence" in data
    assert "probabilities" in data
    assert 0 < data["confidence"] < 1

def test_invalid_pitcher_recommendation():
    payload = {
        "pitcher_name": "Fake Player",
        "balls": 0,
        "strikes": 0,
        "inning": 1,
        "score_diff": 0,
        "on_1b": 0,
        "on_2b": 0,
        "on_3b": 0,
        "batter_hand": "R"
    }
    response = client.post("/recommend/", json=payload)
    assert response.status_code == 404

def test_invalid_ball_count():
    payload = {
        "pitcher_name": "Gerrit Cole",
        "balls": 5,
        "strikes": 0,
        "inning": 1,
        "score_diff": 0,
        "on_1b": 0,
        "on_2b": 0,
        "on_3b": 0,
        "batter_hand": "R"
    }
    response = client.post("/recommend/", json=payload)
    assert response.status_code == 422