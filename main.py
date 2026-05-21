"""
Churn Prediction API

Run with:
    litestar --app main:app run --reload
Then open:
    http://localhost:8000/schema/swagger
"""

import os
from typing import Literal

from litestar import Litestar, get, post
from pydantic import BaseModel, Field

from app.logger_setup import setup_logging
from app.model_utils import predict_churn

# Initialize HyperDX OpenTelemetry instrumentation when an API key is present.
# Set HYPERDX_API_KEY and OTEL_SERVICE_NAME before starting the server.
if os.getenv("HYPERDX_API_KEY"):
    from hyperdx.opentelemetry import configure

    configure(
        service_name=os.getenv("OTEL_SERVICE_NAME", "churn-api"),
        access_token=os.environ["HYPERDX_API_KEY"],
    )

logger = setup_logging()


# ---------------------------------------------------------------------------
# Request Schema
# ---------------------------------------------------------------------------
class ChurnRequest(BaseModel):
    CreditScore: float = Field(ge=300, le=900)
    Geography: Literal["France", "Germany", "Spain"]
    Gender: Literal["Female", "Male"]
    Age: float = Field(ge=18, le=120)
    Tenure: float = Field(ge=0, le=10)
    Balance: float = Field(ge=0)
    NumOfProducts: float = Field(ge=1, le=4)
    HasCrCard: Literal[0, 1]
    IsActiveMember: Literal[0, 1]
    EstimatedSalary: float = Field(ge=0)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@get("/")
async def home() -> dict:
    logger.info("Home endpoint accessed")
    return {"message": "Welcome to the Churn Prediction API"}


@get("/health")
async def health() -> dict:
    logger.info("Health check requested")
    return {"status": "healthy"}


@post("/predict")
async def predict(data: ChurnRequest) -> dict:
    features = [
        data.CreditScore,
        data.Geography,
        data.Gender,
        data.Age,
        data.Tenure,
        data.Balance,
        data.NumOfProducts,
        data.HasCrCard,
        data.IsActiveMember,
        data.EstimatedSalary,
    ]
    logger.info(f"Predict request received: {features}")
    pred = predict_churn(features)
    logger.info(f"Prediction returned: {pred}")
    return {"prediction": pred, "churn": bool(pred)}


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = Litestar(
    route_handlers=[home, health, predict],
)
