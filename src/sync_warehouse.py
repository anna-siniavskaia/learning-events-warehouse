"""Move new MySQL events to PostgreSQL with an atomic watermark."""

from __future__ import annotations

import argparse
import json
import os
from datetime import timezone


SELECT_SOURCE = """
SELECT source_id, event_id, learner_id, event_type, content_id,
       occurred_at, recorded_at, payload
FROM learning_events WHERE source_id > %s ORDER BY source_id LIMIT %s
"""
INSERT_RAW = """
INSERT INTO raw.learning_events
    (source_id, event_id, learner_id, event_type, content_id,
     occurred_at, recorded_at, payload)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
ON CONFLICT (event_id) DO UPDATE SET event_id = EXCLUDED.event_id
WHERE raw.learning_events.source_id = EXCLUDED.source_id
  AND raw.learning_events.learner_id = EXCLUDED.learner_id
  AND raw.learning_events.event_type = EXCLUDED.event_type
  AND raw.learning_events.content_id = EXCLUDED.content_id
  AND raw.learning_events.occurred_at = EXCLUDED.occurred_at
  AND raw.learning_events.recorded_at = EXCLUDED.recorded_at
  AND raw.learning_events.payload = EXCLUDED.payload
RETURNING source_id
"""


def sync_batch(mysql_connection, pg_connection, batch_size: int = 500) -> int:
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    with pg_connection.transaction():
        with pg_connection.cursor() as pg_cursor:
            pg_cursor.execute(
                "SELECT last_source_id FROM etl.watermarks "
                "WHERE pipeline_name = %s FOR UPDATE", ("learning_events",),
            )
            watermark_row = pg_cursor.fetchone()
            if watermark_row is None:
                raise RuntimeError("learning_events watermark is missing")
            watermark = watermark_row[0]
            with mysql_connection.cursor() as mysql_cursor:
                mysql_cursor.execute(SELECT_SOURCE, (watermark, batch_size))
                rows = mysql_cursor.fetchall()
            for row in rows:
                source_id, event_id, learner_id, event_type, content_id, occurred_at, recorded_at, payload = row
                if isinstance(payload, str):
                    payload = json.loads(payload)
                pg_cursor.execute(INSERT_RAW, (
                    source_id, event_id, learner_id, event_type, content_id,
                    occurred_at.replace(tzinfo=timezone.utc),
                    recorded_at.replace(tzinfo=timezone.utc),
                    json.dumps(payload, separators=(",", ":")),
                ))
                if pg_cursor.fetchone() != (source_id,):
                    raise RuntimeError(f"conflicting source data for event {event_id}")
            if rows:
                pg_cursor.execute(
                    "UPDATE etl.watermarks SET last_source_id = %s, updated_at = now() "
                    "WHERE pipeline_name = %s",
                    (rows[-1][0], "learning_events"),
                )
    return len(rows)


def main() -> None:
    import pymysql
    import psycopg

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()
    mysql_connection = pymysql.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "pipeline"),
        password=os.environ["MYSQL_PASSWORD"],
        database=os.getenv("MYSQL_DATABASE", "learning"),
        autocommit=True,
    )
    pg_connection = psycopg.connect(os.environ["POSTGRES_DSN"])
    try:
        total = 0
        while True:
            count = sync_batch(mysql_connection, pg_connection, args.batch_size)
            total += count
            if count < args.batch_size:
                break
    finally:
        mysql_connection.close()
        pg_connection.close()
    print(f"Synced {total} new events to PostgreSQL")


if __name__ == "__main__":
    main()
