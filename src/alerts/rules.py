
from datetime import timedelta

# AI Cloud Monitoring v1.0 thresholds
CPU_LIMIT = 90
RAM_LIMIT = 90
DISK_LIMIT = 95

COOLDOWN_SECONDS = 300


def should_trigger_alert(
    cpu_percent,
    memory_percent,
    disk_percent,
    prediction
):
    """
    Critical alert is triggered by resource thresholds.

    AI prediction is retained for compatibility,
    but is not required to raise a critical alert.
    """
    return (
        cpu_percent >= CPU_LIMIT
        or memory_percent >= RAM_LIMIT
        or disk_percent >= DISK_LIMIT
    )


def get_alert_reason(cpu, ram, disk):
    reasons = []

    if cpu >= CPU_LIMIT:
        reasons.append("HIGH CPU")

    if ram >= RAM_LIMIT:
        reasons.append("HIGH MEMORY")

    if disk >= DISK_LIMIT:
        reasons.append("DISK NEARLY FULL")

    return ", ".join(reasons)


def cooldown_elapsed(
    last_alert_at,
    current_time,
    cooldown_seconds=COOLDOWN_SECONDS
):
    if last_alert_at is None:
        return True

    return (
        current_time - last_alert_at
        >= timedelta(seconds=cooldown_seconds)
    )


def classify_monitoring_event(
    cpu_percent,
    memory_percent,
    disk_percent,
    prediction
):
    """
    Hybrid monitoring classification.
    """
    if should_trigger_alert(
        cpu_percent,
        memory_percent,
        disk_percent,
        prediction
    ):
        return "CRITICAL"

    if prediction == -1:
        return "ANOMALY"

    return "NORMAL"
