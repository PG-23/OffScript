# api/tests/test_matchups.py

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


# ── GET /{pitcher_name} ───────────────────────────────────────────────────

def test_get_pitcher_matchups_valid():
    """Valid pitcher returns a MatchupList with at least one result."""
    response = client.get("/matchups/Chris Sale")
    assert response.status_code == 200
    data = response.json()
    assert data["pitcher_name"] == "Chris Sale"
    assert "matchups" in data
    assert len(data["matchups"]) > 0
    assert "total_matchups" in data


def test_get_pitcher_matchups_structure():
    """Each matchup record contains all required fields with correct types."""
    response = client.get("/matchups/Chris Sale")
    assert response.status_code == 200
    matchup = response.json()["matchups"][0]
    assert "pitcher_name" in matchup
    assert "batter_name" in matchup
    assert "batter_id" in matchup
    assert "stand" in matchup
    assert "matchup_score" in matchup
    assert "exploitation_tier" in matchup
    assert isinstance(matchup["matchup_score"], float)
    assert matchup["stand"] in ("L", "R")


def test_get_pitcher_matchups_invalid():
    """Unknown pitcher returns 404."""
    response = client.get("/matchups/Fake Player")
    assert response.status_code == 404


def test_get_pitcher_matchups_case_insensitive():
    """Pitcher name lookup is case-insensitive."""
    response = client.get("/matchups/chris sale")
    assert response.status_code == 200
    assert response.json()["pitcher_name"] == "Chris Sale"


def test_get_pitcher_matchups_top_n():
    """top_n query parameter limits the number of results returned."""
    response = client.get("/matchups/Chris Sale?top_n=1")
    assert response.status_code == 200
    assert len(response.json()["matchups"]) == 1


def test_get_pitcher_matchups_stand_filter_valid():
    """Filtering by stand='R' returns only right-handed batter matchups."""
    response = client.get("/matchups/Chris Sale?stand=R")
    assert response.status_code == 200
    for matchup in response.json()["matchups"]:
        assert matchup["stand"] == "R"


def test_get_pitcher_matchups_stand_filter_invalid():
    """Invalid stand value returns 400."""
    response = client.get("/matchups/Chris Sale?stand=X")
    assert response.status_code == 400


def test_get_pitcher_matchups_exploitation_tier_values():
    """exploitation_tier values are drawn from the defined tier set."""
    valid_tiers = {
        "Elite Exploitation",
        "High Exploitation",
        "Moderate Exploitation",
        "Low Exploitation",
    }
    response = client.get("/matchups/Chris Sale")
    assert response.status_code == 200
    for matchup in response.json()["matchups"]:
        assert matchup["exploitation_tier"] in valid_tiers


# ── GET /{pitcher_name}/{batter_name} ─────────────────────────────────────

def test_get_specific_matchup_valid():
    """Valid pitcher-batter combination returns matchup data."""
    response = client.get("/matchups/Chris Sale/Mookie Betts")
    assert response.status_code == 200
    data = response.json()
    assert data["pitcher_name"] == "Chris Sale"
    assert data["batter_name"] == "Mookie Betts"
    assert len(data["matchups"]) > 0


def test_get_specific_matchup_invalid():
    """Unknown pitcher-batter combination returns 404."""
    response = client.get("/matchups/Chris Sale/Fake Batter")
    assert response.status_code == 404


def test_get_specific_matchup_score_range():
    """Matchup score is within the valid 0–100 range."""
    response = client.get("/matchups/Chris Sale/Mookie Betts")
    assert response.status_code == 200
    for matchup in response.json()["matchups"]:
        assert 0 <= matchup["matchup_score"] <= 100