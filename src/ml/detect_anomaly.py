
import sys
import time
from pathlib import Path

import joblib
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR / "src"))

from database import get_connection

artifact = joblib.load(
    BASE_DIR / "models" / "isolation_forest.joblib"
)

model = artifact["model"]
features = artifact["features"]


def detect_new_metrics():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    m.id,
                    m.cpu_percent,
                    m.memory_percent,
                    m.disk_percent
                FROM system_metrics m
                LEFT JOIN anomaly_predictions a
                    ON m.id = a.metric_id
                WHERE a.id IS NULL
                ORDER BY m.id
                LIMIT 500
            """)

            rows = cur.fetchall()

            if not rows:
                return 0, 0

            df = pd.DataFrame(
                rows,
                columns=[
                    "id",
                    "cpu_percent",
                    "memory_percent",
                    "disk_percent",
                ],
            )

            predictions = model.predict(df[features])
            scores = model.decision_function(df[features])

            anomaly_count = 0

            for metric_id, pred, score in zip(
                df["id"], predictions, scores
            ):
                cur.execute("""
                    INSERT INTO anomaly_predictions
                    (metric_id, prediction, anomaly_score)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (metric_id) DO NOTHING
                """, (
                    int(metric_id),
                    int(pred),
                    float(score),
                ))

                if pred == -1:
                    anomaly_count += 1

            return len(rows), anomaly_count


def main():
    print("AI detector started. Press Ctrl+C to stop.")

    try:
        while True:
            try:
                count, anomalies = detect_new_metrics()

                if count:
                    print(
                        f"Processed: {count} | "
                        f"Anomalies: {anomalies}"
                    )

            except Exception as error:
                print(f"Detection error: {error}")

            time.sleep(5)

    except KeyboardInterrupt:
        print("AI detector stopped.")


if __name__ == "__main__":
    main()
