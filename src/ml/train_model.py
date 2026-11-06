
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

import sys

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR / "src"))

from database import get_connection

MODEL_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"

MODEL_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

FEATURES = [
    "cpu_percent",
    "memory_percent",
    "disk_percent",
]


def load_data():
    query = """
        SELECT
            timestamp,
            cpu_percent,
            memory_percent,
            disk_percent
        FROM system_metrics
        ORDER BY timestamp ASC
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            records = cur.fetchall()
            columns = [desc.name for desc in cur.description]

    return pd.DataFrame(records, columns=columns)


def main():
    print("Loading data from PostgreSQL...")

    df = load_data()
    print(f"Total records: {len(df)}")

    if len(df) < 200:
        raise ValueError(
            "Minimal 200 records diperlukan untuk demo ini. "
            "Jalankan monitor.py lebih lama."
        )

    # Data cleaning
    df = df.dropna(subset=FEATURES)
    df = df.drop_duplicates(subset=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    # Validasi persentase
    
# Validasi persentase (0 sampai 100)
    valid = (
        (df[FEATURES] >= 0) &
        (df[FEATURES] <= 100)
        ).all(axis=1)
    
    df = df.loc[valid].reset_index(drop=True)

    if len(df) < 200:
        raise ValueError("Data valid kurang dari 200 records.")

    # Split berdasarkan urutan waktu (80% / 20%)
    split = int(len(df) * 0.8)
    train_df = df.iloc[:split].copy()
    test_df = df.iloc[split:].copy()

    model = make_pipeline(
        StandardScaler(),
        IsolationForest(
            n_estimators=200,
            contamination=0.03,
            random_state=42,
            n_jobs=-1,
        ),
    )

    # Hanya melatih pada data training
    model.fit(train_df[FEATURES])

    # Evaluasi data yang lebih baru
    test_df["prediction"] = model.predict(
        test_df[FEATURES]
    )

    test_df["anomaly_score"] = model.decision_function(
        test_df[FEATURES]
    )

    test_df["status"] = test_df["prediction"].map({
        1: "NORMAL",
        -1: "ANOMALY",
    })

    anomaly_count = (test_df["prediction"] == -1).sum()

    print(f"Training records: {len(train_df)}")
    print(f"Testing records: {len(test_df)}")
    print(f"Detected anomalies: {anomaly_count}")

    # Simpan model dan urutan fitur
    joblib.dump(
        {"model": model, "features": FEATURES},
        MODEL_DIR / "isolation_forest.joblib"
    )

    # Simpan hasil prediksi
    test_df.to_csv(
        DATA_DIR / "anomaly_results.csv",
        index=False,
    )

    print("Model saved successfully!")
    print("Results saved to data/anomaly_results.csv")


if __name__ == "__main__":
    main()
