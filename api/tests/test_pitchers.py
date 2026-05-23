# api/tests/test_pitchers.py

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


# ── GET /health ───────────────────────────────────────────────────────────

def test_health_check():
    """Health endpoint returns 200 with expected fields."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert "pitchers_loaded" in data
    assert "version" in data


# ── GET /pitchers/ ────────────────────────────────────────────────────────

def test_get_all_pitchers():
    """All-pitchers endpoint returns a non-empty list with required fields."""
    response = client.get("/pitchers/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "pitcher_name" in data[0]
    assert "deviation_score" in data[0]
    assert "deviation_advantage" in data[0]


def test_get_all_pitchers_sorted_by_deviation():
    """Pitchers are returned in descending deviation score order."""
    response = client.get("/pitchers/")
    assert response.status_code == 200
    scores = [p["deviation_score"] for p in response.json()]
    assert scores == sorted(scores, reverse=True)


# ── GET /pitchers/{pitcher_name} ──────────────────────────────────────────

def test_get_valid_pitcher():
    """Known pitcher returns 200 with correct name and required fields."""
    response = client.get("/pitchers/Gerrit Cole")
    assert response.status_code == 200
    data = response.json()
    assert data["pitcher_name"] == "Gerrit Cole"
    assert "deviation_score" in data
    assert "deviation_advantage" in data
    assert "two_strike_dev_cost" in data
    assert "arsenal_size" in data
    assert "deviation_rank" in data


def test_get_invalid_pitcher():
    """Unknown pitcher returns 404."""
    response = client.get("/pitchers/Fake Player")
    assert response.status_code == 404


def test_get_pitcher_case_insensitive():
    """Pitcher name lookup is case-insensitive."""
    response = client.get("/pitchers/gerrit cole")
    assert response.status_code == 200
    assert response.json()["pitcher_name"] == "Gerrit Cole"


# ── GET /pitchers/{pitcher_name}/arsenal ──────────────────────────────────

def test_pitcher_arsenal_valid():
    """Arsenal endpoint returns pitch distribution summing to ~1.0."""
    response = client.get("/pitchers/Gerrit Cole/arsenal")
    assert response.status_code == 200
    data = response.json()
    assert "arsenal" in data
    assert "total_pitches" in data
    assert len(data["arsenal"]) > 0
    total = sum(data["arsenal"].values())
    assert 0.99 <= total <= 1.01


def test_pitcher_arsenal_invalid():
    """Unknown pitcher returns 404 on arsenal endpoint."""
    response = client.get("/pitchers/Fake Player/arsenal")
    assert response.status_code == 404


# ── GET /pitchers/{pitcher_name}/deviations ───────────────────────────────

def test_pitcher_deviations_valid():
    """Deviations endpoint returns expected structure for a known pitcher."""
    response = client.get("/pitchers/Gerrit Cole/deviations")
    assert response.status_code == 200
    data = response.json()
    assert "pitcher_name" in data
    assert "total_deviations" in data
    assert "deviation_rate" in data
    assert "substitution_patterns" in data
    assert isinstance(data["substitution_patterns"], dict)


def test_pitcher_deviations_invalid():
    """Unknown pitcher returns 404 on deviations endpoint."""
    response = client.get("/pitchers/Fake Player/deviations")
    assert response.status_code == 404


def test_pitcher_deviations_rate_range():
    """Deviation rate is a valid percentage between 0 and 100."""
    response = client.get("/pitchers/Gerrit Cole/deviations")
    assert response.status_code == 200
    assert 0 <= response.json()["deviation_rate"] <= 100