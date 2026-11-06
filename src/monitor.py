
import os
import time
from datetime import datetime

import psutil

from database import insert_metrics

# Windows menggunakan drive C:
# Linux menggunakan root filesystem /
DISK_PATH = "C:\\" if os.name == "nt" else "/"


def collect_metrics():
    return {
        "timestamp": datetime.now(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage(DISK_PATH).percent,
    }


def main():
    print("AI Cloud Monitoring Collector")
    print(f"Monitoring disk path: {DISK_PATH}")

    try:
        while True:
            metrics = collect_metrics()

            try:
                insert_metrics(metrics)
                print(
                    f"CPU: {metrics['cpu_percent']}% | "
                    f"RAM: {metrics['memory_percent']}% | "
                    f"Disk: {metrics['disk_percent']}% | "
                    "SAVED",
                    flush=True,
                )
            except Exception as error:
                print(f"Database error: {error}", flush=True)

            time.sleep(4)

    except KeyboardInterrupt:
        print("Collector stopped.")


if __name__ == "__main__":
    main()
