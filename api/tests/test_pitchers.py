# api/tests/test_pitchers.py

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["model_loaded"] == True

def test_get_all_pitchers():
    response = client.get("/pitchers/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "pitcher_name" in data[0]
    assert "deviation_score" in data[0]

def test_get_valid_pitcher():
    response = client.get("/pitchers/Gerrit Cole")
    assert response.status_code == 200
    data = response.json()
    assert data["pitcher_name"] == "Gerrit Cole"
    assert "deviation_score" in data

def test_get_invalid_pitcher():
    response = client.get("/pitchers/Fake Player")
    assert response.status_code == 404

def test_pitcher_arsenal():
    response = client.get("/pitchers/Gerrit Cole/arsenal")
    assert response.status_code == 200
    data = response.json()
    assert "arsenal" in data
    assert len(data["arsenal"]) > 0