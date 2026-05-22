"""
Load test for the Churn Prediction API.

Run against the deployed EC2 instance:
    uv run locust -f locustfile.py --host http://13.53.152.59:443

Then open http://localhost:8089 and start a swarm:
    Number of users: 100
    Spawn rate:      10 (users/sec)
"""

import random

from locust import HttpUser, between, task

GEOGRAPHIES = ["France", "Germany", "Spain"]
GENDERS = ["Female", "Male"]


def random_customer() -> dict:
    """Build a realistic random churn-prediction payload."""
    return {
        "CreditScore": random.randint(300, 900),
        "Geography": random.choice(GEOGRAPHIES),
        "Gender": random.choice(GENDERS),
        "Age": random.randint(18, 90),
        "Tenure": random.randint(0, 10),
        "Balance": round(random.uniform(0, 250_000), 2),
        "NumOfProducts": random.randint(1, 4),
        "HasCrCard": random.choice([0, 1]),
        "IsActiveMember": random.choice([0, 1]),
        "EstimatedSalary": round(random.uniform(10_000, 200_000), 2),
    }


class ChurnAPIUser(HttpUser):
    """Simulates a user hitting the API. Weights mimic real traffic:
    most requests are predictions, with occasional health/home pings."""

    wait_time = between(0.1, 1.0)

    @task(10)
    def predict(self):
        self.client.post("/predict", json=random_customer(), name="POST /predict")

    @task(2)
    def health(self):
        self.client.get("/health", name="GET /health")

    @task(1)
    def home(self):
        self.client.get("/", name="GET /")
