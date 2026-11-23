"""Generate deterministic fictional learning events as JSON Lines."""

from __future__ import annotations

import argparse
import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

LEVELS = ("A1", "A2", "B1", "B2")
EVENT_TYPES = ("exercise_completed", "text_read", "placement_completed")
START = datetime(2026, 11, 1, tzinfo=timezone.utc)


def generate_events(count: int, seed: int) -> list[dict[str, object]]:
    if count < 0:
        raise ValueError("count must be non-negative")
    rng = random.Random(seed)
    events: list[dict[str, object]] = []
    for number in range(1, count + 1):
        event_type = rng.choice(EVENT_TYPES)
        kind = {
            "exercise_completed": "exercise",
            "text_read": "text",
            "placement_completed": "placement",
        }[event_type]
        occurred_at = START + timedelta(minutes=rng.randrange(7 * 24 * 60))
        recorded_at = occurred_at + timedelta(minutes=rng.randrange(0, 90))
        payload: dict[str, object] = {"level": rng.choice(LEVELS)}
        if event_type == "text_read":
            payload["duration_seconds"] = rng.randint(30, 900)
        else:
            payload["score"] = rng.randint(0, 100)
        events.append({
            "event_id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"learning-events:{seed}:{number}")),
            "learner_id": f"learner-{rng.randint(1, 80):04d}",
            "event_type": event_type,
            "content_id": f"{kind}-{rng.randint(1, 50):03d}",
            "occurred_at": occurred_at.isoformat().replace("+00:00", "Z"),
            "recorded_at": recorded_at.isoformat().replace("+00:00", "Z"),
            "payload": payload,
        })
    return events


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    events = generate_events(args.count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as stream:
        for event in events:
            stream.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"Wrote {len(events)} synthetic events to {args.output}")


if __name__ == "__main__":
    main()
