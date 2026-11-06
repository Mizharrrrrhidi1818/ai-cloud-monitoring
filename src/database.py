
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def get_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        connect_timeout=5,
    )


def insert_metrics(metrics):
    query = """
        INSERT INTO system_metrics (
            timestamp,
            cpu_percent,
            memory_percent,
            disk_percent
        )
        VALUES (%s, %s, %s, %s)
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    metrics["timestamp"],
                    metrics["cpu_percent"],
                    metrics["memory_percent"],
                    metrics["disk_percent"],
                ),
            )


if __name__ == "__main__":
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                print("Koneksi berhasil!")
                print(cur.fetchone()[0])
    except psycopg.Error as error:
        print("Koneksi database gagal:", error)
