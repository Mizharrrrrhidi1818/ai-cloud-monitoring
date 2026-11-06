
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

INPUT = ROOT / "data" / "training" / "vps_metrics_full.csv"

FEATURES = [
    "cpu_percent",
    "memory_percent",
    "disk_percent",
]

print("\n=== VPS DATA QUALITY REPORT ===\n")

df = pd.read_csv(INPUT)

required = ["id", "timestamp", *FEATURES]
missing_columns = set(required) - set(df.columns)

if missing_columns:
    raise ValueError(
        f"Missing columns: {sorted(missing_columns)}"
    )

df["timestamp"] = pd.to_datetime(
    df["timestamp"], errors="coerce"
)

for col in FEATURES:
    df[col] = pd.to_numeric(
        df[col], errors="coerce"
    )

df = df.sort_values(
    ["timestamp", "id"]
).reset_index(drop=True)

print("Total records:", len(df))

missing = df[required].isna().sum()
print("\nMissing values:")
print(missing.to_string())

duplicate_ids = df["id"].duplicated().sum()
print("\nDuplicate IDs:", duplicate_ids)

invalid = (
    (df[FEATURES] < 0)
    | (df[FEATURES] > 100)
).any(axis=1)

print("Out-of-range records:", int(invalid.sum()))

valid_times = df["timestamp"].dropna()

if not valid_times.empty:
    first = valid_times.min()
    last = valid_times.max()
    duration = last - first

    print("\nFirst record:", first)
    print("Last record:", last)
    print("Collection duration:", duration)

    intervals = (
        df["timestamp"]
        .diff()
        .dt.total_seconds()
        .dropna()
    )

    print("\nMedian interval (seconds):",
          intervals.median())

    print("Intervals > 15 seconds:",
          int((intervals > 15).sum()))

print("\nResource statistics:")
print(
    df[FEATURES]
    .describe()
    .round(2)
    .to_string()
)

valid_mask = (
    df[required].notna().all(axis=1)
    & ~invalid
    & ~df["id"].duplicated()
)

clean = df.loc[
    valid_mask, required
].copy()

OUTPUT = (
    ROOT / "data" / "training"
    / "vps_metrics_clean.csv"
)

clean.to_csv(OUTPUT, index=False)

print("\nValid records:", len(clean))
print("Removed records:", len(df) - len(clean))
print("Clean dataset saved:", OUTPUT)

if valid_times.empty:
    print("\nWARNING: No valid timestamps.")
elif duration < pd.Timedelta(hours=24):
    print("\nNOTE: Dataset covers less than 24 hours.")

print("\nData quality check completed.")
