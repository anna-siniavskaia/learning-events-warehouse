import unittest

from src.assert_demo import EXPECTED_DAILY_ACTIVITY, EXPECTED_LEVEL_ACTIVITY, assert_demo


class FakeCursor:
    def __init__(self, daily_activity, level_activity):
        self.daily_activity = daily_activity
        self.level_activity = level_activity
        self.result = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, query):
        normalized = " ".join(query.split())
        if normalized == "SELECT count(*) FROM raw.learning_events":
            self.result = [(100,)]
        elif normalized == "SELECT count(*) FROM mart.fct_learning_event":
            self.result = [(100,)]
        elif normalized == "SELECT count(*) FROM mart.daily_activity":
            self.result = [(7,)]
        elif normalized.startswith("SELECT event_date, active_learners"):
            self.result = self.daily_activity
        elif normalized.startswith("SELECT event_date, level, events"):
            self.result = self.level_activity
        elif "WHERE source_id > 100" in normalized:
            self.result = [(0,)]
        elif "WITH initial AS" in normalized:
            self.result = [(0,)]
        else:
            raise AssertionError(f"unexpected query: {normalized}")

    def fetchone(self):
        return self.result[0]

    def fetchall(self):
        return self.result


class FakeConnection:
    def __init__(self, daily_activity, level_activity=None):
        self.daily_activity = daily_activity
        self.level_activity = level_activity or EXPECTED_LEVEL_ACTIVITY[100]

    def cursor(self):
        return FakeCursor(self.daily_activity, self.level_activity)


class DemoFixtureTests(unittest.TestCase):
    def test_exact_daily_metrics_pass(self):
        assert_demo(FakeConnection(EXPECTED_DAILY_ACTIVITY[100]), 100, 0, 0)

    def test_daily_metric_drift_fails_even_when_counts_match(self):
        changed = list(EXPECTED_DAILY_ACTIVITY[100])
        changed[0] = (*changed[0][:-1], changed[0][-1] + 1)
        with self.assertRaisesRegex(AssertionError, "daily activity mismatch"):
            assert_demo(FakeConnection(changed), 100, 0, 0)

    def test_exact_level_metrics_pass(self):
        assert_demo(
            FakeConnection(EXPECTED_DAILY_ACTIVITY[100], EXPECTED_LEVEL_ACTIVITY[100]),
            100,
            0,
            0,
        )

    def test_level_metric_drift_fails_even_when_counts_match(self):
        changed = list(EXPECTED_LEVEL_ACTIVITY[100])
        changed[0] = (*changed[0][:-1], changed[0][-1] + 1)
        with self.assertRaisesRegex(AssertionError, "level activity mismatch"):
            assert_demo(
                FakeConnection(EXPECTED_DAILY_ACTIVITY[100], changed),
                100,
                0,
                0,
            )


if __name__ == "__main__":
    unittest.main()
