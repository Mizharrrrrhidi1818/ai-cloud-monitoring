
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "src"))

from alerts.rules import cooldown_elapsed


class TestAlertCooldown(unittest.TestCase):

    def setUp(self):
        self.now = datetime(2026, 11, 5, 12, 0, 0)

    def test_first_alert_allowed(self):
        self.assertTrue(
            cooldown_elapsed(None, self.now)
        )

    def test_after_30_seconds_blocked(self):
        previous = self.now - timedelta(seconds=30)
        self.assertFalse(
            cooldown_elapsed(previous, self.now)
        )

    def test_after_4_minutes_blocked(self):
        previous = self.now - timedelta(minutes=4)
        self.assertFalse(
            cooldown_elapsed(previous, self.now)
        )

    def test_exactly_5_minutes_allowed(self):
        previous = self.now - timedelta(minutes=5)
        self.assertTrue(
            cooldown_elapsed(previous, self.now)
        )

    def test_after_6_minutes_allowed(self):
        previous = self.now - timedelta(minutes=6)
        self.assertTrue(
            cooldown_elapsed(previous, self.now)
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
