
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    ROOT / "models" /
    "vps_isolation_forest_candidate.joblib"
)

EVAL_PATH = (
    ROOT / "data" / "training" /
    "vps_model_evaluation.csv"
)

SCENARIO_PATH = (
    ROOT / "data" / "training" /
    "vps_scenario_evaluation.csv"
)

print("\n=== VPS AI MODEL EVALUATION ===\n")

# 1. Load the trained candidate model
artifact = joblib.load(MODEL_PATH)

model = artifact["model"]
features = artifact["features"]

# 2. Read chronological test results
df = pd.read_csv(EVAL_PATH)

required = features + ["prediction", "anomaly_score"]

missing = set(required) - set(df.columns)

if missing:
    raise ValueError(f"Missing columns: {missing}")

# 3. Summarize model predictions
total = len(df)

normal = int((df["prediction"] == 1).sum())
anomaly = int((df["prediction"] == -1).sum())

if total == 0:
    raise ValueError("Evaluation dataset is empty.")

if normal + anomaly != total:
    raise ValueError("Unexpected prediction values.")

rate = anomaly / total * 100

print("=== REAL VPS TEST PERIOD ===")
print(f"Total records: {total}")
print(f"Normal predictions: {normal}")
print(f"Anomaly predictions: {anomaly}")
print(f"Anomaly rate: {rate:.2f}%")

print("\nResource statistics for predicted anomalies:")

anomaly_df = df[df["prediction"] == -1]

if anomaly_df.empty:
    print("No anomalies detected in the test period.")
else:
    print(
        anomaly_df[features]
        .describe()
        .round(2)
        .to_string()
    )

    print("\nFive most unusual records:")

    cols = ["timestamp", *features, "anomaly_score"]

    print(
        anomaly_df.nsmallest(5, "anomaly_score")[cols]
        .to_string(index=False)
    )

# 4. Controlled scenario tests
scenarios = pd.DataFrame([
    {
        "scenario": "Typical VPS workload",
        "cpu_percent": 3,
        "memory_percent": 58,
        "disk_percent": 47,
        "expected": "NORMAL",
    },
    {
        "scenario": "High CPU",
        "cpu_percent": 98,
        "memory_percent": 58,
        "disk_percent": 47,
        "expected": "ANOMALY",
    },
    {
        "scenario": "High RAM",
        "cpu_percent": 3,
        "memory_percent": 98,
        "disk_percent": 47,
        "expected": "ANOMALY",
    },
    {
        "scenario": "Disk almost full",
        "cpu_percent": 3,
        "memory_percent": 58,
        "disk_percent": 99,
        "expected": "ANOMALY",
    },
    {
        "scenario": "Multiple overloads",
        "cpu_percent": 99,
        "memory_percent": 99,
        "disk_percent": 99,
        "expected": "ANOMALY",
    },
    {
        "scenario": "Moderate CPU activity",
        "cpu_percent": 35,
        "memory_percent": 58,
        "disk_percent": 47,
        "expected": "NORMAL",
    },
])

# 5. Make predictions
X = scenarios[features]

scenarios["prediction"] = model.predict(X)
scenarios["score"] = model.decision_function(X)

scenarios["actual"] = scenarios["prediction"].map({
    1: "NORMAL",
    -1: "ANOMALY",
})

scenarios["match"] = (
    scenarios["actual"] == scenarios["expected"]
)

print("\n=== CONTROLLED SCENARIO RESULTS ===")

print(
    scenarios[
        ["scenario", "expected", "actual", "score", "match"]
    ].to_string(index=False)
)

matched = int(scenarios["match"].sum())

print(
    f"\nScenario agreement: {matched}/{len(scenarios)}"
)

# 6. Save scenario evaluation
SCENARIO_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)

scenarios.to_csv(SCENARIO_PATH, index=False)

print("\nScenario evaluation saved:")
print(SCENARIO_PATH)

print("\nEvaluation completed.")
