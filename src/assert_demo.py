"""Assert exact fixture outcomes after fresh, replay, and late-event runs."""

from __future__ import annotations

import argparse
import os
from datetime import date
from decimal import Decimal


EXPECTED_DAILY_ACTIVITY = {
    100: [
        (date(2026, 11, 1), 13, 4, 3, 7, Decimal("41.45"), Decimal("58.25")),
        (date(2026, 11, 2), 17, 8, 5, 7, Decimal("42.98"), Decimal("47.50")),
        (date(2026, 11, 3), 12, 6, 5, 2, Decimal("14.65"), Decimal("52.17")),
        (date(2026, 11, 4), 16, 2, 10, 5, Decimal("28.18"), Decimal("41.00")),
        (date(2026, 11, 5), 11, 4, 2, 5, Decimal("34.32"), Decimal("61.25")),
        (date(2026, 11, 6), 7, 4, 2, 2, Decimal("11.42"), Decimal("76.75")),
        (date(2026, 11, 7), 16, 7, 6, 4, Decimal("44.17"), Decimal("43.86")),
    ],
    110: [
        (date(2026, 11, 1), 14, 5, 4, 7, Decimal("41.45"), Decimal("51.20")),
        (date(2026, 11, 2), 20, 9, 6, 8, Decimal("53.28"), Decimal("43.56")),
        (date(2026, 11, 3), 12, 6, 5, 2, Decimal("14.65"), Decimal("52.17")),
        (date(2026, 11, 4), 18, 3, 11, 6, Decimal("42.57"), Decimal("47.00")),
        (date(2026, 11, 5), 12, 4, 3, 5, Decimal("34.32"), Decimal("61.25")),
        (date(2026, 11, 6), 7, 4, 2, 2, Decimal("11.42"), Decimal("76.75")),
        (date(2026, 11, 7), 17, 7, 6, 5, Decimal("51.38"), Decimal("43.86")),
    ],
}

EXPECTED_LEVEL_ACTIVITY = {
    100: [
        (date(2026, 11, 1), "A1", 7, 7, Decimal("63.67")),
        (date(2026, 11, 1), "A2", 2, 2, None),
        (date(2026, 11, 1), "B2", 5, 5, Decimal("42.00")),
        (date(2026, 11, 2), "A1", 4, 4, Decimal("31.00")),
        (date(2026, 11, 2), "A2", 5, 5, Decimal("60.67")),
        (date(2026, 11, 2), "B1", 6, 6, None),
        (date(2026, 11, 2), "B2", 5, 5, Decimal("41.75")),
        (date(2026, 11, 3), "A1", 4, 4, Decimal("44.00")),
        (date(2026, 11, 3), "A2", 1, 1, None),
        (date(2026, 11, 3), "B1", 2, 2, Decimal("39.00")),
        (date(2026, 11, 3), "B2", 6, 6, Decimal("73.50")),
        (date(2026, 11, 4), "A1", 4, 4, Decimal("48.00")),
        (date(2026, 11, 4), "A2", 4, 4, Decimal("34.00")),
        (date(2026, 11, 4), "B1", 5, 5, None),
        (date(2026, 11, 4), "B2", 4, 4, None),
        (date(2026, 11, 5), "A1", 1, 1, None),
        (date(2026, 11, 5), "A2", 2, 2, None),
        (date(2026, 11, 5), "B1", 5, 5, Decimal("72.33")),
        (date(2026, 11, 5), "B2", 3, 3, Decimal("28.00")),
        (date(2026, 11, 6), "A1", 1, 1, Decimal("50.00")),
        (date(2026, 11, 6), "A2", 2, 2, Decimal("91.00")),
        (date(2026, 11, 6), "B1", 3, 2, Decimal("81.00")),
        (date(2026, 11, 6), "B2", 2, 2, Decimal("85.00")),
        (date(2026, 11, 7), "A1", 6, 5, Decimal("79.00")),
        (date(2026, 11, 7), "A2", 3, 3, Decimal("45.00")),
        (date(2026, 11, 7), "B1", 5, 5, Decimal("46.00")),
        (date(2026, 11, 7), "B2", 3, 3, Decimal("0.00")),
    ],
    110: [
        (date(2026, 11, 1), "A1", 8, 8, Decimal("53.50")),
        (date(2026, 11, 1), "A2", 2, 2, None),
        (date(2026, 11, 1), "B2", 6, 6, Decimal("42.00")),
        (date(2026, 11, 2), "A1", 4, 4, Decimal("31.00")),
        (date(2026, 11, 2), "A2", 6, 6, Decimal("48.50")),
        (date(2026, 11, 2), "B1", 7, 7, None),
        (date(2026, 11, 2), "B2", 6, 6, Decimal("41.75")),
        (date(2026, 11, 3), "A1", 4, 4, Decimal("44.00")),
        (date(2026, 11, 3), "A2", 1, 1, None),
        (date(2026, 11, 3), "B1", 2, 2, Decimal("39.00")),
        (date(2026, 11, 3), "B2", 6, 6, Decimal("73.50")),
        (date(2026, 11, 4), "A1", 5, 5, Decimal("48.00")),
        (date(2026, 11, 4), "A2", 6, 6, Decimal("46.50")),
        (date(2026, 11, 4), "B1", 5, 5, None),
        (date(2026, 11, 4), "B2", 4, 4, None),
        (date(2026, 11, 5), "A1", 1, 1, None),
        (date(2026, 11, 5), "A2", 3, 3, None),
        (date(2026, 11, 5), "B1", 5, 5, Decimal("72.33")),
        (date(2026, 11, 5), "B2", 3, 3, Decimal("28.00")),
        (date(2026, 11, 6), "A1", 1, 1, Decimal("50.00")),
        (date(2026, 11, 6), "A2", 2, 2, Decimal("91.00")),
        (date(2026, 11, 6), "B1", 3, 2, Decimal("81.00")),
        (date(2026, 11, 6), "B2", 2, 2, Decimal("85.00")),
        (date(2026, 11, 7), "A1", 6, 5, Decimal("79.00")),
        (date(2026, 11, 7), "A2", 3, 3, Decimal("45.00")),
        (date(2026, 11, 7), "B1", 5, 5, Decimal("46.00")),
        (date(2026, 11, 7), "B2", 4, 4, Decimal("0.00")),
    ],
}


def assert_demo(connection, expected_events: int, expected_late: int, expected_first_seen_corrections: int) -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM raw.learning_events")
        raw_count = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM mart.fct_learning_event")
        fact_count = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM mart.daily_activity")
        day_count = cursor.fetchone()[0]
        cursor.execute("""
            SELECT event_date, active_learners, exercises_completed,
                   placement_tests, texts_read, reading_minutes,
                   average_exercise_score
            FROM mart.daily_activity
            ORDER BY event_date
        """)
        daily_activity = cursor.fetchall()
        cursor.execute("""
            SELECT event_date, level, events, active_learners,
                   average_exercise_score
            FROM mart.level_activity
            ORDER BY event_date, level
        """)
        level_activity = cursor.fetchall()
        cursor.execute("""
            SELECT count(*) FROM raw.learning_events
            WHERE source_id > 100
              AND occurred_at < (
                  SELECT max(occurred_at) FROM raw.learning_events WHERE source_id <= 100
              )
        """)
        late_count = cursor.fetchone()[0]
        cursor.execute("""
            WITH initial AS (
                SELECT learner_id, min(occurred_at) AS first_seen
                FROM raw.learning_events WHERE source_id <= 100 GROUP BY learner_id
            ), later AS (
                SELECT learner_id, min(occurred_at) AS first_seen
                FROM raw.learning_events WHERE source_id > 100 GROUP BY learner_id
            )
            SELECT count(*) FROM initial
            JOIN later USING (learner_id)
            WHERE later.first_seen < initial.first_seen
        """)
        corrections = cursor.fetchone()[0]
    observed = (raw_count, fact_count, day_count, late_count, corrections)
    expected = (expected_events, expected_events, 7, expected_late, expected_first_seen_corrections)
    if observed != expected:
        raise AssertionError(f"demo fixture mismatch: observed {observed}, expected {expected}")
    expected_daily_activity = EXPECTED_DAILY_ACTIVITY.get(expected_events)
    if expected_daily_activity is None:
        raise AssertionError(f"no daily metric fixture is defined for {expected_events} events")
    if daily_activity != expected_daily_activity:
        raise AssertionError(
            "daily activity mismatch: "
            f"observed {daily_activity}, expected {expected_daily_activity}"
        )
    expected_level_activity = EXPECTED_LEVEL_ACTIVITY.get(expected_events)
    if expected_level_activity is None:
        raise AssertionError(f"no level metric fixture is defined for {expected_events} events")
    if level_activity != expected_level_activity:
        raise AssertionError(
            "level activity mismatch: "
            f"observed {level_activity}, expected {expected_level_activity}"
        )
    print(
        f"Demo fixture verified: {raw_count} events, {day_count} days, "
        f"{late_count} late events, exact daily and level metrics"
    )


def main() -> None:
    import psycopg

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-events", type=int, required=True)
    parser.add_argument("--expected-late", type=int, required=True)
    parser.add_argument("--expected-first-seen-corrections", type=int, required=True)
    args = parser.parse_args()
    with psycopg.connect(os.environ["POSTGRES_DSN"]) as connection:
        assert_demo(
            connection,
            args.expected_events,
            args.expected_late,
            args.expected_first_seen_corrections,
        )


if __name__ == "__main__":
    main()
