"""Reconcile source IDs and event IDs across the two databases."""

from __future__ import annotations

import os


def check_pipeline(mysql_connection, pg_connection) -> int:
    with mysql_connection.cursor() as cursor:
        cursor.execute("SELECT source_id, event_id FROM learning_events ORDER BY source_id")
        source_rows = cursor.fetchall()
    with pg_connection.cursor() as cursor:
        cursor.execute("SELECT source_id, event_id::text FROM raw.learning_events ORDER BY source_id")
        warehouse_rows = cursor.fetchall()
        cursor.execute(
            "SELECT last_source_id FROM etl.watermarks WHERE pipeline_name = %s",
            ("learning_events",),
        )
        watermark_row = cursor.fetchone()
    if watermark_row is None:
        raise RuntimeError("learning_events watermark is missing")
    if list(source_rows) != list(warehouse_rows):
        raise RuntimeError("source and warehouse event IDs or source IDs differ")
    expected_watermark = source_rows[-1][0] if source_rows else 0
    if watermark_row[0] != expected_watermark:
        raise RuntimeError(
            f"watermark {watermark_row[0]} differs from maximum source ID {expected_watermark}"
        )
    return len(source_rows)


def main() -> None:
    import pymysql
    import psycopg

    mysql_connection = pymysql.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "pipeline"),
        password=os.environ["MYSQL_PASSWORD"],
        database=os.getenv("MYSQL_DATABASE", "learning"),
    )
    pg_connection = psycopg.connect(os.environ["POSTGRES_DSN"])
    try:
        count = check_pipeline(mysql_connection, pg_connection)
    finally:
        mysql_connection.close()
        pg_connection.close()
    print(f"Reconciled {count} source and warehouse events; watermark matches")


if __name__ == "__main__":
    main()
