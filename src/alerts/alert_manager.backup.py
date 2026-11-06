
import sys
import time
from pathlib import Path

from psycopg import errors

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR / "src"))

from database import get_connection

CPU_LIMIT = 90
RAM_LIMIT = 90
DISK_LIMIT = 95

COOLDOWN_SECONDS = 300


def check_alerts():
    query = """
        SELECT
            m.id,
            m.timestamp,
            m.cpu_percent,
            m.memory_percent,
            m.disk_percent
        FROM anomaly_predictions a
        JOIN system_metrics m
            ON m.id = a.metric_id
        LEFT JOIN system_alerts sa
            ON sa.metric_id = m.id
        WHERE a.prediction = -1
          AND sa.id IS NULL
          AND m.timestamp >= CURRENT_TIMESTAMP
              - INTERVAL '2 minutes'
          AND (
              m.cpu_percent >= %s
              OR m.memory_percent >= %s
              OR m.disk_percent >= %s
          )
        ORDER BY m.timestamp, m.id
        LIMIT 100
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (CPU_LIMIT, RAM_LIMIT, DISK_LIMIT)
            )
            rows = cur.fetchall()

            if not rows:
                return 0

            # Cek peringatan terakhir
            cur.execute("""
                SELECT created_at
                FROM system_alerts
                ORDER BY created_at DESC
                LIMIT 1
            """)

            last = cur.fetchone()

            from datetime import datetime

            if last is not None:
                elapsed = (
                    datetime.now() - last[0]
                ).total_seconds()

                if elapsed < COOLDOWN_SECONDS:
                    return 0

            metric_id, ts, cpu, ram, disk = rows[-1]

            message = (
                f"CRITICAL | Time: {ts} | "
                f"CPU: {cpu:.1f}% | "
                f"RAM: {ram:.1f}% | "
                f"Disk: {disk:.1f}%"
            )

            cur.execute("""
                INSERT INTO system_alerts
                (metric_id, severity, message)
                VALUES (%s, %s, %s)
                ON CONFLICT (metric_id) DO NOTHING
                RETURNING id
            """, (metric_id, "CRITICAL", message))

            if cur.fetchone() is not None:
                print("\n" + "=" * 55)
                print("🚨 AI CLOUD MONITORING ALERT")
                print(message)
                print("=" * 55 + "\n")
                return 1

            return 0


def main():
    print("Alert manager started.")
    print("Monitoring critical anomalies...")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            try:
                check_alerts()
            except Exception as error:
                print(f"Alert error: {error}")

            time.sleep(5)

    except KeyboardInterrupt:
        print("Alert manager stopped.")


if __name__ == "__main__":
    main()
