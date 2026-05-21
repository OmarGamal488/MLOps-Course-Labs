"""
Model loading and prediction logic.

The model must be loaded ONCE at module level, NOT inside the predict function.
"""

import joblib
import pandas as pd

FEATURES = [
    "CreditScore",
    "Geography",
    "Gender",
    "Age",
    "Tenure",
    "Balance",
    "NumOfProducts",
    "HasCrCard",
    "IsActiveMember",
    "EstimatedSalary",
]

model = joblib.load("data/model.joblib")


def predict_churn(features: list) -> int:
    """
    Takes a list of feature values and returns a churn prediction (0 or 1).
    """
    df = pd.DataFrame([features], columns=FEATURES)
    return int(model.predict(df)[0])


if __name__ == "__main__":
    sample = [650, "France", "Female", 40, 3, 60000.0, 2, 1, 1, 50000.0]
    print(f"Input:      {sample}")
    print(f"Prediction: {predict_churn(sample)}")
