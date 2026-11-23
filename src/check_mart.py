"""Fail when the dimensional mart diverges from the raw event table."""

from __future__ import annotations

import os


def check_mart(connection) -> int:
    with connection.cursor() as cursor:
        cursor.execute("SELECT count(*), coalesce(max(source_id), 0) FROM raw.learning_events")
        raw_count, raw_max_id = cursor.fetchone()
        cursor.execute("SELECT count(*) FROM mart.fct_learning_event")
        fact_count = cursor.fetchone()[0]
        cursor.execute(
            "SELECT last_source_id FROM mart.refresh_state WHERE model_name = %s",
            ("learning_events",),
        )
        state = cursor.fetchone()
        if state is None or (raw_count, raw_max_id) != (fact_count, state[0]):
            raise RuntimeError("mart fact count or watermark differs from raw events")
        cursor.execute("""
            SELECT count(*) FROM raw.learning_events r
            JOIN mart.fct_learning_event f USING (event_id)
            WHERE r.source_id IS DISTINCT FROM f.source_id
               OR r.learner_id IS DISTINCT FROM f.learner_id
               OR r.content_id IS DISTINCT FROM f.content_id
               OR r.event_type IS DISTINCT FROM f.event_type
               OR r.occurred_at IS DISTINCT FROM f.occurred_at
               OR (r.occurred_at AT TIME ZONE 'UTC')::date IS DISTINCT FROM f.event_date
               OR r.payload->>'level' IS DISTINCT FROM f.level
               OR (r.payload->>'score')::integer IS DISTINCT FROM f.score
               OR (r.payload->>'duration_seconds')::integer IS DISTINCT FROM f.duration_seconds
        """)
        if cursor.fetchone()[0]:
            raise RuntimeError("mart fact attributes differ from raw events")
        cursor.execute("""
            SELECT count(*) FROM mart.dim_learner d
            FULL OUTER JOIN (
                SELECT learner_id, min(occurred_at) AS first_seen_at
                FROM raw.learning_events GROUP BY learner_id
            ) expected USING (learner_id)
            WHERE d.learner_id IS NULL
               OR expected.learner_id IS NULL
               OR d.first_seen_at IS DISTINCT FROM expected.first_seen_at
        """)
        if cursor.fetchone()[0]:
            raise RuntimeError("learner dimension differs from raw events")
        cursor.execute("""
            SELECT count(*) FROM mart.dim_content d
            FULL OUTER JOIN (
                SELECT DISTINCT content_id, event_type
                FROM raw.learning_events
            ) expected USING (content_id)
            WHERE d.content_id IS NULL
               OR expected.content_id IS NULL
               OR d.event_type IS DISTINCT FROM expected.event_type
        """)
        if cursor.fetchone()[0]:
            raise RuntimeError("content dimension differs from raw events")
        cursor.execute("SELECT coalesce(sum(exercises_completed + placement_tests + texts_read), 0) FROM mart.daily_activity")
        if cursor.fetchone()[0] != fact_count:
            raise RuntimeError("daily activity event totals differ from mart facts")
    return fact_count


def main() -> None:
    import psycopg

    connection = psycopg.connect(os.environ["POSTGRES_DSN"])
    try:
        count = check_mart(connection)
    finally:
        connection.close()
    print(f"Checked {count} mart facts against raw events and daily activity")


if __name__ == "__main__":
    main()
