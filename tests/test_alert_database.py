
import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "src"))

from database import get_connection
from alerts.alert_manager import insert_critical_alert


class TestAlertDatabase(unittest.TestCase):

    def setUp(self):
        self.conn = get_connection()
        self.cur = self.conn.cursor()

        # TEMP TABLE shadows the real system_alerts table
        # only inside this database session.
        self.cur.execute("""
            CREATE TEMP TABLE system_alerts (
                id BIGSERIAL PRIMARY KEY,
                metric_id BIGINT NOT NULL UNIQUE,
                severity VARCHAR(20) NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            ) ON COMMIT DROP
        """)

    def tearDown(self):
        # Never commit test records.
        self.conn.rollback()
        self.cur.close()
        self.conn.close()

    def test_insert_critical_alert(self):
        alert_id = insert_critical_alert(
            self.cur, 1001, 95, 50, 40, -1
        )

        self.assertIsNotNone(alert_id)

        self.cur.execute(
            "SELECT COUNT(*) FROM system_alerts"
        )
        self.assertEqual(self.cur.fetchone()[0], 1)

    def test_normal_does_not_insert(self):
        alert_id = insert_critical_alert(
            self.cur, 1002, 20, 40, 40, 1
        )
        self.assertIsNone(alert_id)

    def test_cooldown_blocks_second_alert(self):
        first = insert_critical_alert(
            self.cur, 1003, 96, 50, 40, -1
        )
        second = insert_critical_alert(
            self.cur, 1004, 97, 50, 40, -1
        )

        self.assertIsNotNone(first)
        self.assertIsNone(second)

        self.cur.execute(
            "SELECT COUNT(*) FROM system_alerts"
        )
        self.assertEqual(self.cur.fetchone()[0], 1)

    def test_after_cooldown_allows_new_alert(self):
        first = insert_critical_alert(
            self.cur, 1005, 96, 50, 40, -1
        )

        self.assertIsNotNone(first)

        # Simulate alert created six minutes ago.
        self.cur.execute("""
            UPDATE system_alerts
            SET created_at =
                CURRENT_TIMESTAMP - INTERVAL '6 minutes'
        """)

        second = insert_critical_alert(
            self.cur, 1006, 97, 50, 40, -1
        )

        self.assertIsNotNone(second)


if __name__ == "__main__":
    unittest.main(verbosity=2)
