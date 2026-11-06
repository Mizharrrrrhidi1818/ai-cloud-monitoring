
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]

csv_file = BASE_DIR / "data" / "anomaly_results.csv"
output_file = BASE_DIR / "dashboards" / "cpu_anomalies.png"

df = pd.read_csv(csv_file, parse_dates=["timestamp"])

anomalies = df[df["prediction"] == -1]

plt.figure(figsize=(12, 5))

plt.plot(
    df["timestamp"],
    df["cpu_percent"],
    label="CPU Usage",
    color="steelblue",
)

plt.scatter(
    anomalies["timestamp"],
    anomalies["cpu_percent"],
    color="red",
    label="Detected Anomaly",
    s=55,
    zorder=3,
)

plt.title("AI Cloud Monitoring - CPU Anomaly Detection")
plt.xlabel("Timestamp")
plt.ylabel("CPU Usage (%)")
plt.ylim(0, 105)
plt.legend()
plt.grid(alpha=0.3)
plt.xticks(rotation=30)
plt.tight_layout()

plt.savefig(output_file, dpi=150)
plt.show()

print(f"Chart saved: {output_file}")
