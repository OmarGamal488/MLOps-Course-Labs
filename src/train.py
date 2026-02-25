"""
This module contains functions to preprocess and train the model
for bank consumer churn prediction.
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.utils import resample
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.compose import make_column_transformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    ConfusionMatrixDisplay,
)

import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
from mlflow.tracking import MlflowClient


def rebalance(data):
    """
    Resample data to keep balance between target classes.

    The function uses the resample function to downsample the majority class to match the minority class.

    Args:
        data (pd.DataFrame): DataFrame

    Returns:
        pd.DataFrame): balanced DataFrame
    """
    churn_0 = data[data["Exited"] == 0]
    churn_1 = data[data["Exited"] == 1]
    if len(churn_0) > len(churn_1):
        churn_maj = churn_0
        churn_min = churn_1
    else:
        churn_maj = churn_1
        churn_min = churn_0
    churn_maj_downsample = resample(
        churn_maj, n_samples=len(churn_min), replace=False, random_state=1234
    )

    return pd.concat([churn_maj_downsample, churn_min])


def preprocess(df):
    """
    Preprocess and split data into training and test sets.

    Args:
        df (pd.DataFrame): DataFrame with features and target variables

    Returns:
        ColumnTransformer: ColumnTransformer with scalers and encoders
        pd.DataFrame: training set with transformed features
        pd.DataFrame: test set with transformed features
        pd.Series: training set target
        pd.Series: test set target
    """
    filter_feat = [
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
        "Exited",
    ]
    cat_cols = ["Geography", "Gender"]
    num_cols = [
        "CreditScore",
        "Age",
        "Tenure",
        "Balance",
        "NumOfProducts",
        "HasCrCard",
        "IsActiveMember",
        "EstimatedSalary",
    ]
    data = df.loc[:, filter_feat]
    data_bal = rebalance(data=data)
    X = data_bal.drop("Exited", axis=1)
    y = data_bal["Exited"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=1912
    )
    col_transf = make_column_transformer(
        (StandardScaler(), num_cols),
        (OneHotEncoder(handle_unknown="ignore", drop="first"), cat_cols),
        remainder="passthrough",
    )

    X_train = col_transf.fit_transform(X_train)
    X_train = pd.DataFrame(X_train, columns=col_transf.get_feature_names_out())

    X_test = col_transf.transform(X_test)
    X_test = pd.DataFrame(X_test, columns=col_transf.get_feature_names_out())

    mlflow.sklearn.log_model(col_transf, artifact_path="column_transformer")

    return col_transf, X_train, X_test, y_train, y_test


def train(model, X_train, y_train):
    """
    Train a given sklearn model.

    Args:
        model: sklearn estimator
        X_train (pd.DataFrame): DataFrame with features
        y_train (pd.Series): Series with target

    Returns:
        trained sklearn estimator
    """
    model.fit(X_train, y_train)

    signature = infer_signature(X_train, model.predict(X_train))
    mlflow.sklearn.log_model(model, artifact_path="model", signature=signature)

    mlflow.log_input(mlflow.data.from_pandas(X_train), context="training")

    return model


def run_experiment(df, model, params, model_type):
    """Run a single MLflow experiment for a given model configuration."""
    with mlflow.start_run(run_name=model_type) as run:
        col_transf, X_train, X_test, y_train, y_test = preprocess(df)

        mlflow.log_params(params)

        trained_model = train(model, X_train, y_train)

        y_pred = trained_model.predict(X_test)

        mlflow.log_metrics({
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred),
            "recall": recall_score(y_test, y_pred),
            "f1": f1_score(y_test, y_pred),
        })

        mlflow.set_tag("model_type", model_type)

        conf_mat = confusion_matrix(y_test, y_pred, labels=trained_model.classes_)
        conf_mat_disp = ConfusionMatrixDisplay(
            confusion_matrix=conf_mat, display_labels=trained_model.classes_
        )
        conf_mat_disp.plot()
        plt.title(f"Confusion Matrix — {model_type}")
        plt.savefig("confusion_matrix.png")
        mlflow.log_artifact("confusion_matrix.png")
        plt.close()

        return run.info.run_id


def main():
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("churn-prediction")

    df = pd.read_csv("Churn_Modelling.csv")

    experiments = [
        (
            LogisticRegression(max_iter=1000, C=1.0, solver="lbfgs"),
            {"max_iter": 1000, "C": 1.0, "solver": "lbfgs"},
            "LogisticRegression",
        ),
        (
            RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42),
            {"n_estimators": 200, "max_depth": 10, "random_state": 42},
            "RandomForest",
        ),
        (
            GradientBoostingClassifier(
                n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42
            ),
            {"n_estimators": 100, "learning_rate": 0.1, "max_depth": 3, "random_state": 42},
            "GradientBoosting",
        ),
    ]

    run_ids = {}
    for model, params, model_type in experiments:
        print(f"\n>>> Running experiment: {model_type}")
        run_id = run_experiment(df, model, params, model_type)
        run_ids[model_type] = run_id
        print(f"    Run ID: {run_id}")

    client = MlflowClient()
    experiment = client.get_experiment_by_name("churn-prediction")

    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["metrics.f1 DESC"],
    )

    print("\n=== Experiment Results (sorted by F1) ===")
    for r in runs:
        m = r.data.metrics
        print(
            f"  {r.data.tags.get('model_type', 'unknown'):25s} | "
            f"F1={m.get('f1', 0):.4f}  "
            f"Recall={m.get('recall', 0):.4f}  "
            f"Precision={m.get('precision', 0):.4f}  "
            f"Accuracy={m.get('accuracy', 0):.4f}"
        )

    best_run = runs[0]
    second_run = runs[1]
    best_model_type = best_run.data.tags.get("model_type", "unknown")
    second_model_type = second_run.data.tags.get("model_type", "unknown")

    model_name = "churn-classifier"

    best_model_uri = f"runs:/{best_run.info.run_id}/model"
    second_model_uri = f"runs:/{second_run.info.run_id}/model"

    best_mv = mlflow.register_model(best_model_uri, model_name)
    second_mv = mlflow.register_model(second_model_uri, model_name)

    client.transition_model_version_stage(
        name=model_name, version=best_mv.version, stage="Production"
    )
    client.transition_model_version_stage(
        name=model_name, version=second_mv.version, stage="Staging"
    )

    print(f"\n=== Model Registration ===")
    print(f"  PRODUCTION  v{best_mv.version}: {best_model_type}")
    print(
        f"Highest F1={best_run.data.metrics.get('f1', 0):.4f} and "
        f"Recall={best_run.data.metrics.get('recall', 0):.4f}. ")
    print(f"\n  STAGING     v{second_mv.version}: {second_model_type}")
    print(
        f"Second-best F1={second_run.data.metrics.get('f1', 0):.4f}. "
        "Strong candidate for promotion after further validation on held-out")


if __name__ == "__main__":
    main()
