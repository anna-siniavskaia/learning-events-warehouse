"""Demonstrate mart rollback on one invalid raw event, then restore the lab."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import psycopg

from src.build_mart import build_batch
from src.check_mart import check_mart


EVENT_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, "learning-events:recovery-check"))
LEARNER_ID = "learner-9999"
CONTENT_ID = "exercise-999"


class ExpectedDriftRollback(Exception):
    """Roll back a temporary quality-check mutation after it is detected."""


def verify_dimension_drift(connection, insert_sql: str, expected_message: str) -> None:
    try:
        with connection.transaction():
            with connection.cursor() as cursor:
                cursor.execute(insert_sql)
            try:
                check_mart(connection)
            except RuntimeError as error:
                if expected_message not in str(error):
                    raise
                raise ExpectedDriftRollback from error
            raise AssertionError(f"{expected_message} was not detected")
    except ExpectedDriftRollback:
        pass


def main() -> None:
    connection = psycopg.connect(os.environ["POSTGRES_DSN"], autocommit=True)
    original_watermark = None
    inserted = False
    try:
        original_count = check_mart(connection)
        verify_dimension_drift(
            connection,
            "INSERT INTO mart.dim_learner (learner_id, first_seen_at) "
            "VALUES ('learner-9998', '2026-11-01T00:00:00Z')",
            "learner dimension",
        )
        verify_dimension_drift(
            connection,
            "INSERT INTO mart.dim_content (content_id, event_type) "
            "VALUES ('exercise-998', 'exercise_completed')",
            "content dimension",
        )
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    (SELECT count(*) FROM raw.learning_events WHERE event_id = %s),
                    (SELECT count(*) FROM mart.dim_learner WHERE learner_id = %s),
                    (SELECT count(*) FROM mart.dim_content WHERE content_id = %s)
            """, (EVENT_ID, LEARNER_ID, CONTENT_ID))
            if any(cursor.fetchone()):
                raise RuntimeError("reserved recovery-test IDs already exist")
            cursor.execute("SELECT last_source_id FROM mart.refresh_state WHERE model_name = %s", ("learning_events",))
            original_watermark = cursor.fetchone()[0]
            cursor.execute("SELECT coalesce(max(source_id), 0) + 1 FROM raw.learning_events")
            test_source_id = cursor.fetchone()[0]
            cursor.execute("""
                INSERT INTO raw.learning_events
                    (event_id, source_id, learner_id, event_type, content_id,
                     occurred_at, recorded_at, payload)
                VALUES (%s, %s, %s, 'exercise_completed', %s, %s, %s,
                        '{"level":"A1","score":999}'::jsonb)
            """, (
                EVENT_ID, test_source_id, LEARNER_ID, CONTENT_ID,
                datetime(2026, 11, 1, tzinfo=timezone.utc),
                datetime(2026, 11, 1, 1, tzinfo=timezone.utc),
            ))
            inserted = True
        try:
            build_batch(connection)
        except psycopg.errors.CheckViolation:
            pass
        else:
            raise AssertionError("invalid score did not stop mart refresh")
        with connection.cursor() as cursor:
            cursor.execute("SELECT last_source_id FROM mart.refresh_state WHERE model_name = %s", ("learning_events",))
            if cursor.fetchone()[0] != original_watermark:
                raise AssertionError("mart watermark advanced after failed batch")
            cursor.execute("SELECT count(*) FROM mart.dim_learner WHERE learner_id = %s", (LEARNER_ID,))
            if cursor.fetchone()[0] != 0:
                raise AssertionError("dimension insert was not rolled back")
            cursor.execute("SELECT count(*) FROM mart.fct_learning_event WHERE event_id = %s", (EVENT_ID,))
            if cursor.fetchone()[0] != 0:
                raise AssertionError("invalid fact was retained")
    finally:
        try:
            if inserted:
                with connection.transaction():
                    with connection.cursor() as cursor:
                        cursor.execute("DELETE FROM mart.fct_learning_event WHERE event_id = %s", (EVENT_ID,))
                        cursor.execute("DELETE FROM mart.dim_content WHERE content_id = %s", (CONTENT_ID,))
                        cursor.execute("DELETE FROM mart.dim_learner WHERE learner_id = %s", (LEARNER_ID,))
                        cursor.execute("DELETE FROM raw.learning_events WHERE event_id = %s", (EVENT_ID,))
                        if original_watermark is not None:
                            cursor.execute(
                                "UPDATE mart.refresh_state SET last_source_id = %s WHERE model_name = %s",
                                (original_watermark, "learning_events"),
                            )
        finally:
            connection.close()
    with psycopg.connect(os.environ["POSTGRES_DSN"]) as restored_connection:
        if check_mart(restored_connection) != original_count:
            raise AssertionError("mart count changed after recovery check")
    print("Dimension drift detected; invalid fact rolled back with the watermark; test rows removed")


if __name__ == "__main__":
    main()
