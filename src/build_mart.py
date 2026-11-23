"""Incrementally build dimensional tables from PostgreSQL raw events."""

from __future__ import annotations

import argparse
import os


INSERT_LEARNERS = """
INSERT INTO mart.dim_learner (learner_id, first_seen_at)
SELECT learner_id, min(occurred_at)
FROM raw.learning_events
WHERE source_id > %s AND source_id <= %s
GROUP BY learner_id
ON CONFLICT (learner_id) DO UPDATE
SET first_seen_at = least(mart.dim_learner.first_seen_at, EXCLUDED.first_seen_at)
"""

INSERT_CONTENT = """
INSERT INTO mart.dim_content (content_id, event_type)
SELECT DISTINCT content_id, event_type
FROM raw.learning_events
WHERE source_id > %s AND source_id <= %s
ON CONFLICT (content_id) DO NOTHING
"""

INSERT_FACTS = """
INSERT INTO mart.fct_learning_event
    (event_id, source_id, learner_id, content_id, event_type, event_date,
     occurred_at, level, score, duration_seconds)
SELECT
    event_id, source_id, learner_id, content_id, event_type,
    (occurred_at AT TIME ZONE 'UTC')::date,
    occurred_at,
    payload->>'level',
    (payload->>'score')::integer,
    (payload->>'duration_seconds')::integer
FROM raw.learning_events
WHERE source_id > %s AND source_id <= %s
ON CONFLICT (event_id) DO NOTHING
"""


def build_batch(connection, batch_size: int = 500) -> int:
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT last_source_id FROM mart.refresh_state "
                "WHERE model_name = %s FOR UPDATE", ("learning_events",),
            )
            state = cursor.fetchone()
            if state is None:
                raise RuntimeError("learning_events mart state is missing")
            previous_id = state[0]
            cursor.execute(
                "SELECT source_id FROM raw.learning_events "
                "WHERE source_id > %s ORDER BY source_id LIMIT %s",
                (previous_id, batch_size),
            )
            source_ids = cursor.fetchall()
            if not source_ids:
                return 0
            last_id = source_ids[-1][0]
            bounds = (previous_id, last_id)
            cursor.execute(INSERT_LEARNERS, bounds)
            cursor.execute(INSERT_CONTENT, bounds)
            cursor.execute(INSERT_FACTS, bounds)
            if cursor.rowcount != len(source_ids):
                raise RuntimeError("fact row count differs from incremental batch size")
            cursor.execute(
                "UPDATE mart.refresh_state SET last_source_id = %s, updated_at = now() "
                "WHERE model_name = %s",
                (last_id, "learning_events"),
            )
    return len(source_ids)


def main() -> None:
    import psycopg

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()
    connection = psycopg.connect(os.environ["POSTGRES_DSN"])
    try:
        total = 0
        while True:
            count = build_batch(connection, args.batch_size)
            total += count
            if count < args.batch_size:
                break
    finally:
        connection.close()
    print(f"Built {total} new mart facts")


if __name__ == "__main__":
    main()
