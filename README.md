# Bank Customer Churn Prediction

An MLOps project that trains and tracks machine learning models to predict bank customer churn, using **MLflow** for experiment tracking, model registry, and artifact management.

---

## Project Structure

```
MLOps-Course-Labs/
├── src/
│   └── train.py          # Preprocessing, training, experiment tracking, model registration
├── dataset/
│   └── note.txt          # Link to download the dataset
├── Churn_Modelling.csv   # Dataset (place at project root)
├── requirements.txt      # Pinned Python dependencies
└── README.md
```

---

## Dataset

Bank customer churn dataset from Kaggle.
Download it from: https://www.kaggle.com/datasets/shantanudhakadd/bank-customer-churn-prediction/data

Place the downloaded `Churn_Modelling.csv` file at the **project root**.

**Features used:**

| Feature | Description |
|---|---|
| CreditScore | Customer credit score |
| Geography | Country (France, Germany, Spain) |
| Gender | Male / Female |
| Age | Customer age |
| Tenure | Years with the bank |
| Balance | Account balance |
| NumOfProducts | Number of bank products used |
| HasCrCard | Has credit card (0/1) |
| IsActiveMember | Active member (0/1) |
| EstimatedSalary | Estimated annual salary |
| **Exited** | **Target — churned (1) or not (0)** |

---

## Setup

### 1. Install uv

```bash
pip install uv
```

### 2. Create virtual environment and install dependencies

```bash
uv venv .venv
uv pip install -r requirements.txt
```

### 3. Activate the environment

```bash
source .venv/bin/activate
```

---

## Running the Project

### 1. Start the MLflow tracking server

```bash
mlflow server --host 127.0.0.1 --port 5000
```

### 2. Run training

From the **project root**:

```bash
python src/train.py
```

This will:
- Run three experiments (Logistic Regression, Random Forest, Gradient Boosting)
- Log parameters, metrics, and artifacts to MLflow
- Register the two best models to the MLflow Model Registry
- Promote the best model to **Production** and the second-best to **Staging**

### 3. Open the MLflow UI

```bash
http://localhost:5000
```

---

## Models & Results

Three models are trained and compared on the same preprocessed dataset:

| Model | F1 | Recall | Precision | Accuracy |
|---|---|---|---|---|
| **GradientBoosting** | 0.7651 | 0.7504 | 0.7803 | 0.7735 |
| **RandomForest** | 0.7557 | 0.7388 | 0.7735 | 0.7653 |
| LogisticRegression | 0.6955 | 0.6822 | 0.7093 | 0.7065 |

### Why these metrics?

For churn prediction, **recall** is the most important metric — a false negative (missing an actual churner) is far more costly than a false positive. **F1** is used as the primary ranking metric to balance recall and precision.

---

## Model Registry

Both top models are registered under the name `churn-classifier`:

| Stage | Model | Justification |
|---|---|---|
| **Production** | GradientBoosting | Best F1 (0.7651) and best Recall (0.7504) across all runs |
| **Staging** | RandomForest | Second-best F1 (0.7557); candidate for promotion after live validation |

---

## What is Tracked per Run

- **Parameters** — model hyperparameters (e.g. `n_estimators`, `max_iter`, `learning_rate`)
- **Metrics** — accuracy, precision, recall, F1
- **Artifacts** — fitted column transformer, trained model with signature, confusion matrix image
- **Dataset** — training data logged as an MLflow dataset input
- **Tag** — `model_type` for easy filtering in the UI

---

## Dependencies

```
mlflow==2.22.0
scikit-learn==1.6.1
pandas==2.2.3
numpy==2.2.5
scipy==1.15.2
cloudpickle==3.1.1
psutil==5.9.0
```
