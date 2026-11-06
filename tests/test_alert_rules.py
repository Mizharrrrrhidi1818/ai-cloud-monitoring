
import sys
import unittest
from pathlib import Path

# Project root
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "src"))

from alerts.rules import (
    should_trigger_alert,
    get_alert_reason,
    CPU_LIMIT,
    RAM_LIMIT,
    DISK_LIMIT,
)


class TestAlertRules(unittest.TestCase):
    """
    Final AI Cloud Monitoring v1.0 alert tests.

    Critical resource alerts are independent
    of Isolation Forest predictions.
    """

    def test_normal_system(self):
        result = should_trigger_alert(
            20, 45, 40, 1
        )
        self.assertFalse(result)

    def test_high_cpu_anomaly(self):
        result = should_trigger_alert(
            95, 50, 40, -1
        )
        self.assertTrue(result)

    def test_high_ram_anomaly(self):
        result = should_trigger_alert(
            30, 96, 40, -1
        )
        self.assertTrue(result)

    def test_disk_nearly_full(self):
        result = should_trigger_alert(
            20, 50, 98, -1
        )
        self.assertTrue(result)

    def test_high_cpu_but_normal_prediction(self):
        # Critical CPU must trigger even if AI = NORMAL
        result = should_trigger_alert(
            95, 50, 40, 1
        )
        self.assertTrue(result)

    def test_anomaly_below_threshold(self):
        # Anomaly alone is not a CRITICAL resource alert
        result = should_trigger_alert(
            45, 55, 60, -1
        )
        self.assertFalse(result)

    def test_exact_threshold(self):
        result = should_trigger_alert(
            90, 50, 40, -1
        )
        self.assertTrue(result)

    def test_multiple_critical_resources(self):
        result = should_trigger_alert(
            99, 98, 99, -1
        )
        self.assertTrue(result)

    def test_alert_reason(self):
        reason = get_alert_reason(
            95, 96, 50
        )

        self.assertIn("HIGH CPU", reason)
        self.assertIn("HIGH MEMORY", reason)

    def test_disk_full_with_normal_ai(self):
        # Regression test for the VPS evaluation issue
        result = should_trigger_alert(
            3, 58, 99, 1
        )
        self.assertTrue(result)

    def test_ai_anomaly_without_critical_resource(self):
        result = should_trigger_alert(
            35, 58, 47, -1
        )
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
