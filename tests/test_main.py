"""
Tests for the Churn Prediction API.

Run with:
    pytest tests/ -v
    pytest tests/ -v --cov=app --cov=main --cov-report=term-missing
"""

from litestar.testing import TestClient

from app.model_utils import predict_churn
from main import app


SAMPLE = {
    "CreditScore": 650,
    "Geography": "France",
    "Gender": "Female",
    "Age": 40,
    "Tenure": 3,
    "Balance": 60000,
    "NumOfProducts": 2,
    "HasCrCard": 1,
    "IsActiveMember": 1,
    "EstimatedSalary": 50000,
}


# ---------------------------------------------------------------------------
# Function Tests
# ---------------------------------------------------------------------------
def test_predict_churn_function():
    result = predict_churn([650, "France", "Female", 40, 3, 60000.0, 2, 1, 1, 50000.0])
    assert result in (0, 1)


def test_predict_churn_edge_high_risk():
    # older, inactive, low balance — a high churn-risk profile
    result = predict_churn([400, "Germany", "Male", 70, 1, 0.0, 1, 0, 0, 20000.0])
    assert result in (0, 1)


# ---------------------------------------------------------------------------
# Endpoint Tests
# ---------------------------------------------------------------------------
def test_home():
    with TestClient(app=app) as client:
        r = client.get("/")
        assert r.status_code == 200
        assert "message" in r.json()


def test_health():
    with TestClient(app=app) as client:
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "healthy"}


def test_predict_endpoint():
    with TestClient(app=app) as client:
        r = client.post("/predict", json=SAMPLE)
        assert r.status_code == 201
        body = r.json()
        assert body["prediction"] in (0, 1)
        assert isinstance(body["churn"], bool)


def test_predict_invalid_input_returns_400():
    with TestClient(app=app) as client:
        bad = {**SAMPLE, "CreditScore": "not-a-number"}
        r = client.post("/predict", json=bad)
        assert r.status_code == 400
