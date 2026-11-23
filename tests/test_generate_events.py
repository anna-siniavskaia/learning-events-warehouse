import unittest
from datetime import datetime

from src.generate_events import generate_events


class GenerateEventsTests(unittest.TestCase):
    def test_replay_is_deterministic_and_ids_are_unique(self):
        first = generate_events(100, 42)
        self.assertEqual(first, generate_events(100, 42))
        self.assertEqual(len({event["event_id"] for event in first}), 100)
        self.assertNotEqual(first, generate_events(100, 43))

    def test_late_occurrence_and_recording_order(self):
        events = generate_events(100, 42)
        occurred = [datetime.fromisoformat(event["occurred_at"].replace("Z", "+00:00")) for event in events]
        recorded = [datetime.fromisoformat(event["recorded_at"].replace("Z", "+00:00")) for event in events]
        self.assertTrue(any(a > b for a, b in zip(occurred, occurred[1:])))
        self.assertTrue(all(recorded_at >= occurred_at for occurred_at, recorded_at in zip(occurred, recorded)))
        self.assertTrue(all(event["learner_id"].startswith("learner-") for event in events))
        self.assertGreaterEqual(len({timestamp.date() for timestamp in occurred}), 3)


if __name__ == "__main__":
    unittest.main()
