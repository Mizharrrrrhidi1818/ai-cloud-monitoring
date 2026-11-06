
import csv
from pathlib import Path

from database import get_connection

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_FILE = BASE_DIR / "data" / "system_metrics.csv"


def import_csv():
    if not CSV_FILE.exists():
        print("File CSV tidak ditemukan.")
        return

    inserted = 0

    with get_connection() as conn:
        with conn.cursor() as cur:
            with open(CSV_FILE, newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)

                for row in reader:
                    cur.execute(
                        """
                        INSERT INTO system_metrics (
                            timestamp,
                            cpu_percent,
                            memory_percent,
                            disk_percent
                        )
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (timestamp) DO NOTHING
                        """,
                        (
                            row["timestamp"],
                            float(row["cpu_percent"]),
                            float(row["memory_percent"]),
                            float(row["disk_percent"]),
                        ),
                    )
                    inserted += cur.rowcount

    print(f"Import selesai. {inserted} record baru disimpan.")


if __name__ == "__main__":
    import_csv()
