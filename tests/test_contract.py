import json
import unittest
from pathlib import Path

from src.generate_events import generate_events

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:
    Draft202012Validator = None
    FormatChecker = None


@unittest.skipUnless(Draft202012Validator, "jsonschema is installed in the Docker runner")
class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        contract = Path(__file__).resolve().parents[1] / "contracts/learning_event.schema.json"
        schema = json.loads(contract.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        cls.validator = Draft202012Validator(schema, format_checker=FormatChecker())
        cls.events = generate_events(100, 42)

    def test_all_generated_events_follow_contract(self):
        for event in self.events:
            with self.subTest(event_id=event["event_id"]):
                self.validator.validate(event)

    def test_content_id_must_match_event_type(self):
        for kind in ("exercise_completed", "text_read", "placement_completed"):
            event = next(event for event in self.events if event["event_type"] == kind)
            changed = {**event, "content_id": "text-001" if kind != "text_read" else "exercise-001"}
            with self.subTest(kind=kind):
                self.assertFalse(self.validator.is_valid(changed))

    def test_invalid_score_and_reading_duration_are_rejected(self):
        exercise = next(event for event in self.events if event["event_type"] == "exercise_completed")
        reading = next(event for event in self.events if event["event_type"] == "text_read")
        self.assertFalse(self.validator.is_valid({**exercise, "payload": {"level": "A1", "score": 101}}))
        self.assertFalse(self.validator.is_valid({**reading, "payload": {"level": "A1", "duration_seconds": 0}}))


if __name__ == "__main__":
    unittest.main()
