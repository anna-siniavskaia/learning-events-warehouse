"""Emit a machine-readable health snapshot for the learning event pipeline."""

from __future__ import annotations

import json
import os


def collect_health(mysql_connection, pg_connection) -> dict[str, int | str | bool]:
    with mysql_connection.cursor() as cursor:
        cursor.execute("SELECT count(*), coalesce(max(source_id), 0) FROM learning_events")
        source_count, source_max_id = cursor.fetchone()

    with pg_connection.cursor() as cursor:
        cursor.execute("SELECT count(*), coalesce(max(source_id), 0) FROM raw.learning_events")
        raw_count, raw_max_id = cursor.fetchone()
        cursor.execute("SELECT count(*), coalesce(max(source_id), 0) FROM mart.fct_learning_event")
        fact_count, fact_max_id = cursor.fetchone()
        cursor.execute(
            "SELECT last_source_id FROM etl.watermarks WHERE pipeline_name = %s",
            ("learning_events",),
        )
        ingestion_state = cursor.fetchone()
        cursor.execute(
            "SELECT last_source_id FROM mart.refresh_state WHERE model_name = %s",
            ("learning_events",),
        )
        mart_state = cursor.fetchone()

    if ingestion_state is None or mart_state is None:
        raise RuntimeError("pipeline or mart watermark is missing")

    ingestion_watermark = ingestion_state[0]
    mart_watermark = mart_state[0]
    healthy = (
        source_count == raw_count == fact_count
        and source_max_id == raw_max_id == fact_max_id
        and source_max_id == ingestion_watermark == mart_watermark
    )
    return {
        "status": "healthy" if healthy else "degraded",
        "healthy": healthy,
        "source_events": source_count,
        "raw_events": raw_count,
        "fact_events": fact_count,
        "source_max_id": source_max_id,
        "raw_max_id": raw_max_id,
        "fact_max_id": fact_max_id,
        "ingestion_watermark": ingestion_watermark,
        "mart_watermark": mart_watermark,
        "ingestion_lag": source_max_id - ingestion_watermark,
        "mart_lag": raw_max_id - mart_watermark,
    }


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
        report = collect_health(mysql_connection, pg_connection)
    finally:
        mysql_connection.close()
        pg_connection.close()
    print(json.dumps(report, sort_keys=True))
    if not report["healthy"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
