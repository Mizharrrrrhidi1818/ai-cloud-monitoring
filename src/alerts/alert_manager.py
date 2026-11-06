
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR / "src"))

from database import get_connection
from alerts.rules import (
    should_trigger_alert,
    get_alert_reason,
    COOLDOWN_SECONDS,
)


def insert_critical_alert(
    cursor, metric_id, cpu, ram, disk, prediction
):
    """Insert alert only if rules and cooldown allow it."""

    if not should_trigger_alert(
        cpu, ram, disk, prediction
    ):
        return None

    reason = get_alert_reason(cpu, ram, disk)

    message = (
        f"CRITICAL | {reason} | "
        f"CPU: {cpu:.1f}% | "
        f"RAM: {ram:.1f}% | "
        f"Disk: {disk:.1f}%"
    )

    # PostgreSQL checks cooldown using database time.
    # ON CONFLICT prevents duplicate alerts for one metric.
    cursor.execute(
        """
        INSERT INTO system_alerts (
            metric_id, severity, message
        )
        SELECT %s, 'CRITICAL', %s
        WHERE NOT EXISTS (
            SELECT 1
            FROM system_alerts
            WHERE created_at >=
                CURRENT_TIMESTAMP -
                (%s * INTERVAL '1 second')
        )
        ON CONFLICT (metric_id) DO NOTHING
        RETURNING id
        """,
        (metric_id, message, COOLDOWN_SECONDS),
    )

    result = cursor.fetchone()
    return result[0] if result else None


def check_alerts():
    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    m.id,
                    m.cpu_percent,
                    m.memory_percent,
                    m.disk_percent,
                    a.prediction
                FROM anomaly_predictions a
                JOIN system_metrics m
                    ON m.id = a.metric_id
                LEFT JOIN system_alerts sa
                    ON sa.metric_id = m.id
                WHERE sa.id IS NULL
                  AND m.timestamp >=
                      CURRENT_TIMESTAMP -
                      INTERVAL '2 minutes'
                ORDER BY m.timestamp DESC, m.id DESC
                LIMIT 100
                """
            )

            rows = cur.fetchall()

            for metric_id, cpu, ram, disk, pred in rows:
                alert_id = insert_critical_alert(
                    cur, metric_id, cpu, ram, disk, pred
                )

                if alert_id is not None:
                    print(
                        f"CRITICAL ALERT #{alert_id} | "
                        f"Metric: {metric_id}",
                        flush=True,
                    )
                    return 1

    return 0


def main():
    print("AI Alert Manager started.", flush=True)

    try:
        while True:
            try:
                check_alerts()
            except Exception as error:
                print(
                    f"Alert error: {error}",
                    flush=True,
                )

            time.sleep(5)

    except KeyboardInterrupt:
        print("Alert Manager stopped.")


if __name__ == "__main__":
    main()
