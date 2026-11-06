
from pathlib import Path

import joblib
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]

artifact = joblib.load(
    BASE_DIR / "models" / "isolation_forest.joblib"
)

model = artifact["model"]
features = artifact["features"]

# Data simulasi untuk eksperimen
samples = pd.DataFrame([
    {"cpu_percent": 20, "memory_percent": 40, "disk_percent": 60},
    {"cpu_percent": 35, "memory_percent": 50, "disk_percent": 60},
    {"cpu_percent": 99, "memory_percent": 95, "disk_percent": 99},
    {"cpu_percent": 95, "memory_percent": 90, "disk_percent": 60},
])

samples["prediction"] = model.predict(samples[features])
samples["score"] = model.decision_function(samples[features])

samples["status"] = samples["prediction"].map({
    1: "NORMAL",
    -1: "ANOMALY"
})

print(samples.to_string(index=False))
