
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = ROOT / "data" / "training" / "vps_metrics_clean.csv"

MODEL_PATH = (
    ROOT / "models" / "vps_isolation_forest_candidate.joblib"
)

RESULT_PATH = (
    ROOT / "data" / "training" / "vps_model_evaluation.csv"
)

FEATURES = [
    "cpu_percent",
    "memory_percent",
    "disk_percent",
]

print("\n=== VPS ISOLATION FOREST RETRAINING ===\n")

# 1. Read dataset
df = pd.read_csv(DATA_PATH)

df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="raise"
)

df = df.sort_values(
    ["timestamp", "id"]
).reset_index(drop=True)

# 2. Validate dataset
if len(df) < 200:
    raise ValueError("At least 200 records are required.")

if df[FEATURES].isna().any().any():
    raise ValueError("Missing feature values found.")

# Validate CPU, RAM, and disk percentages
valid_percentages = (
    (df[FEATURES] >= 0)
    & (df[FEATURES] <= 100)
)

if not valid_percentages.all().all():
    raise ValueError("Invalid resource percentages.")

# 3. Chronological split
split_index = int(len(df) * 0.80)

train_df = df.iloc[:split_index].copy()
test_df = df.iloc[split_index:].copy()

X_train = train_df[FEATURES]
X_test = test_df[FEATURES]

print("Total records:", len(df))
print("Training records:", len(train_df))
print("Testing records:", len(test_df))

print("\nTraining period:")
print(train_df["timestamp"].min())
print(train_df["timestamp"].max())

print("\nTesting period:")
print(test_df["timestamp"].min())
print(test_df["timestamp"].max())

# 4. Pipeline prevents fitting the scaler
# on the future test data.
pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("isolation_forest", IsolationForest(
        n_estimators=200,
        contamination=0.03,
        random_state=42,
        n_jobs=-1,
    )),
])

# 5. Train
print("\nTraining model...")
pipeline.fit(X_train)

# 6. Evaluate on held-out time period
predictions = pipeline.predict(X_test)
scores = pipeline.decision_function(X_test)

test_df["prediction"] = predictions
test_df["anomaly_score"] = scores

normal_count = int((predictions == 1).sum())
anomaly_count = int((predictions == -1).sum())

anomaly_rate = (
    anomaly_count / len(predictions) * 100
)

print("\n=== EVALUATION RESULTS ===")
print("Normal predictions:", normal_count)
print("Anomaly predictions:", anomaly_count)
print(f"Anomaly rate: {anomaly_rate:.2f}%")

print("\nDecision score statistics:")
print(pd.Series(scores).describe().round(4))

# 7. Save evaluation results
RESULT_PATH.parent.mkdir(
    parents=True, exist_ok=True
)

test_df.to_csv(RESULT_PATH, index=False)

# 8. Save candidate model
MODEL_PATH.parent.mkdir(
    parents=True, exist_ok=True
)

artifact = {
    "model": pipeline,
    "features": FEATURES,
    "training_source": "SumoPod Ubuntu VPS",
    "training_records": len(train_df),
    "contamination": 0.03,
}

joblib.dump(artifact, MODEL_PATH)

print("\nCandidate model saved:")
print(MODEL_PATH)

print("\nEvaluation CSV saved:")
print(RESULT_PATH)

print("\nTraining completed successfully.")
