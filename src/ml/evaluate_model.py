
from pathlib import Path

import joblib
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_FILE = BASE_DIR / "models" / "isolation_forest.joblib"

artifact = joblib.load(MODEL_FILE)
model = artifact["model"]
features = artifact["features"]

# Skenario pengujian buatan
scenarios = pd.DataFrame([
    {
        "scenario": "Idle system",
        "cpu_percent": 15,
        "memory_percent": 40,
        "disk_percent": 60
    },
    {
        "scenario": "Normal workload",
        "cpu_percent": 45,
        "memory_percent": 55,
        "disk_percent": 60
    },
    {
        "scenario": "High CPU load",
        "cpu_percent": 98,
        "memory_percent": 55,
        "disk_percent": 60
    },
    {
        "scenario": "High RAM usage",
        "cpu_percent": 35,
        "memory_percent": 97,
        "disk_percent": 60
    },
    {
        "scenario": "Disk nearly full",
        "cpu_percent": 30,
        "memory_percent": 50,
        "disk_percent": 99
    },
    {
        "scenario": "Multiple resources overloaded",
        "cpu_percent": 99,
        "memory_percent": 98,
        "disk_percent": 99
    },
])

scenarios["prediction"] = model.predict(
    scenarios[features]
)

scenarios["anomaly_score"] = model.decision_function(
    scenarios[features]
)

scenarios["status"] = scenarios["prediction"].map({
    1: "NORMAL",
    -1: "ANOMALY"
})

print("\nAI MODEL EVALUATION")
print(scenarios[
    ["scenario", "status", "anomaly_score"]
].to_string(index=False))

output = BASE_DIR / "data" / "evaluation_results.csv"
scenarios.to_csv(output, index=False)

print(f"\nResults saved: {output}")
