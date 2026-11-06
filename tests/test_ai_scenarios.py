
from pathlib import Path

import joblib
import pandas as pd

# Lokasi folder utama proyek
BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_PATH = BASE_DIR / "models" / "isolation_forest.joblib"
OUTPUT_PATH = BASE_DIR / "data" / "ai_scenario_results.csv"

# Load model AI
artifact = joblib.load(MODEL_PATH)

model = artifact["model"]
features = artifact["features"]

# Simulasi kondisi server
scenarios = pd.DataFrame([
    {
        "scenario": "Normal workload",
        "cpu_percent": 20,
        "memory_percent": 45,
        "disk_percent": 40,
        "expected": "NORMAL"
    },
    {
        "scenario": "High CPU",
        "cpu_percent": 98,
        "memory_percent": 45,
        "disk_percent": 40,
        "expected": "ANOMALY"
    },
    {
        "scenario": "High RAM",
        "cpu_percent": 20,
        "memory_percent": 98,
        "disk_percent": 40,
        "expected": "ANOMALY"
    },
    {
        "scenario": "Disk nearly full",
        "cpu_percent": 20,
        "memory_percent": 45,
        "disk_percent": 99,
        "expected": "ANOMALY"
    },
    {
        "scenario": "Multiple overloads",
        "cpu_percent": 99,
        "memory_percent": 99,
        "disk_percent": 99,
        "expected": "ANOMALY"
    }
])

# Prediksi menggunakan Isolation Forest
scenarios["prediction"] = model.predict(
    scenarios[features]
)

scenarios["score"] = model.decision_function(
    scenarios[features]
)

# Ubah hasil prediksi menjadi status
scenarios["actual"] = scenarios["prediction"].map({
    1: "NORMAL",
    -1: "ANOMALY"
})

# Bandingkan dengan ekspektasi
scenarios["match"] = (
    scenarios["expected"] == scenarios["actual"]
)

print("\nAI SCENARIO TEST RESULTS\n")

print(
    scenarios[
        ["scenario", "expected", "actual", "score", "match"]
    ].to_string(index=False)
)

print(
    "\nMatched scenarios:",
    int(scenarios["match"].sum()),
    "/",
    len(scenarios)
)

# Simpan hasil pengujian
OUTPUT_PATH.parent.mkdir(exist_ok=True)

scenarios.to_csv(OUTPUT_PATH, index=False)

print(f"\nResults saved: {OUTPUT_PATH}")
