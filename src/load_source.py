"""Load validated JSONL events into the MySQL source table."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


INSERT_EVENT = """
INSERT INTO learning_events
    (event_id, learner_id, event_type, content_id, occurred_at, recorded_at, payload)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE event_id = event_id
"""
SELECT_EXISTING = """
SELECT learner_id, event_type, content_id, occurred_at, recorded_at, payload
FROM learning_events WHERE event_id = %s
"""


def mysql_utc_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("event timestamps must include a UTC offset")
    return parsed.astimezone(timezone.utc).replace(tzinfo=None)


def load_jsonl(path: Path, connection, validator) -> int:
    count = 0
    with path.open(encoding="utf-8") as stream:
        with connection.cursor() as cursor:
            for line_number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                    validator.validate(event)
                    values = (
                        event["event_id"], event["learner_id"], event["event_type"],
                        event["content_id"], mysql_utc_timestamp(event["occurred_at"]),
                        mysql_utc_timestamp(event["recorded_at"]),
                        json.dumps(event["payload"], separators=(",", ":")),
                    )
                    cursor.execute(INSERT_EVENT, values)
                    if cursor.rowcount == 0:
                        cursor.execute(SELECT_EXISTING, (event["event_id"],))
                        existing = cursor.fetchone()
                        if existing is None or existing[:5] != values[1:6] or json.loads(existing[5]) != event["payload"]:
                            raise ValueError("event_id already exists with different content")
                except Exception as exc:
                    connection.rollback()
                    raise ValueError(f"invalid event at {path}:{line_number}: {exc}") from exc
                count += 1
    connection.commit()
    return count


def main() -> None:
    import pymysql
    from jsonschema import Draft202012Validator, FormatChecker

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", type=Path)
    args = parser.parse_args()
    contract = Path(__file__).resolve().parents[1] / "contracts/learning_event.schema.json"
    schema = json.loads(contract.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    connection = pymysql.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "pipeline"),
        password=os.environ["MYSQL_PASSWORD"],
        database=os.getenv("MYSQL_DATABASE", "learning"),
        autocommit=False,
    )
    try:
        count = load_jsonl(args.jsonl, connection, validator)
    finally:
        connection.close()
    print(f"Processed {count} validated events for MySQL (identical duplicates ignored)")


if __name__ == "__main__":
    main()
