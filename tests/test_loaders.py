import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from src.generate_events import generate_events
from src.check_pipeline import check_pipeline
from src.check_mart import check_mart
from src.build_mart import build_batch
from src.load_source import load_jsonl, mysql_utc_timestamp
from src.sync_warehouse import sync_batch


class SourceLoadingTests(unittest.TestCase):
    def test_utc_conversion_and_source_commit(self):
        self.assertEqual(
            mysql_utc_timestamp("2026-11-01T03:30:00+03:00"),
            datetime(2026, 11, 1, 0, 30),
        )
        event = generate_events(1, 42)[0]
        connection = MagicMock()
        validator = MagicMock()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "events.jsonl"
            path.write_text(json.dumps(event) + "\n", encoding="utf-8")
            self.assertEqual(load_jsonl(path, connection, validator), 1)
        validator.validate.assert_called_once_with(event)
        connection.cursor.return_value.__enter__.return_value.execute.assert_called_once()
        connection.commit.assert_called_once()
        connection.rollback.assert_not_called()

    def test_invalid_line_rolls_back_entire_file(self):
        connection = MagicMock()
        validator = MagicMock()
        validator.validate.side_effect = [None, ValueError("bad contract")]
        events = generate_events(2, 42)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "events.jsonl"
            path.write_text("\n".join(json.dumps(event) for event in events), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "events.jsonl:2"):
                load_jsonl(path, connection, validator)
        connection.rollback.assert_called_once()
        connection.commit.assert_not_called()

    def test_changed_duplicate_is_rejected(self):
        event = generate_events(1, 42)[0]
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.rowcount = 0
        cursor.fetchone.return_value = (
            event["learner_id"], event["event_type"], event["content_id"],
            mysql_utc_timestamp(event["occurred_at"]),
            mysql_utc_timestamp(event["recorded_at"]),
            '{"level":"B2","score":101}',
        )
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "events.jsonl"
            path.write_text(json.dumps(event), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "different content"):
                load_jsonl(path, connection, MagicMock())
        connection.rollback.assert_called_once()
        connection.commit.assert_not_called()


class WarehouseSyncTests(unittest.TestCase):
    def setUp(self):
        self.mysql = MagicMock()
        self.pg = MagicMock()
        self.mysql_cursor = self.mysql.cursor.return_value.__enter__.return_value
        self.pg_cursor = self.pg.cursor.return_value.__enter__.return_value
        self.row = (
            7, "55594b5f-3a69-58ca-92da-4b79c8bd5ba5", "learner-0001",
            "text_read", "text-001", datetime(2026, 11, 1, 10),
            datetime(2026, 11, 1, 11), '{"level":"A1","duration_seconds":90}',
        )

    def test_watermark_advances_only_after_insert(self):
        self.mysql_cursor.fetchall.return_value = [self.row]
        self.pg_cursor.fetchone.side_effect = [(0,), (7,)]
        self.assertEqual(sync_batch(self.mysql, self.pg), 1)
        self.mysql_cursor.execute.assert_called_once()
        self.assertEqual(self.mysql_cursor.execute.call_args.args[1], (0, 500))
        self.assertEqual(self.pg_cursor.execute.call_args.args[1], (7, "learning_events"))
        self.assertEqual(self.pg_cursor.execute.call_count, 3)

    def test_conflict_aborts_before_watermark_update(self):
        self.mysql_cursor.fetchall.return_value = [self.row]
        self.pg_cursor.fetchone.side_effect = [(0,), None]
        with self.assertRaisesRegex(RuntimeError, "conflicting source data"):
            sync_batch(self.mysql, self.pg)
        self.assertEqual(self.pg_cursor.execute.call_count, 2)
        self.assertIsNotNone(self.pg.transaction.return_value.__exit__.call_args.args[0])

    def test_empty_batch_leaves_watermark_unchanged(self):
        self.mysql_cursor.fetchall.return_value = []
        self.pg_cursor.fetchone.return_value = (7,)
        self.assertEqual(sync_batch(self.mysql, self.pg), 0)
        self.assertEqual(self.pg_cursor.execute.call_count, 1)


class ReconciliationTests(unittest.TestCase):
    def test_driver_result_container_types_do_not_affect_reconciliation(self):
        mysql = MagicMock()
        pg = MagicMock()
        mysql.cursor.return_value.__enter__.return_value.fetchall.return_value = ((7, "event-7"),)
        pg_cursor = pg.cursor.return_value.__enter__.return_value
        pg_cursor.fetchall.return_value = [(7, "event-7")]
        pg_cursor.fetchone.return_value = (7,)
        self.assertEqual(check_pipeline(mysql, pg), 1)

    def test_missing_warehouse_row_fails(self):
        mysql = MagicMock()
        pg = MagicMock()
        mysql.cursor.return_value.__enter__.return_value.fetchall.return_value = ((7, "event-7"),)
        pg_cursor = pg.cursor.return_value.__enter__.return_value
        pg_cursor.fetchall.return_value = []
        pg_cursor.fetchone.return_value = (7,)
        with self.assertRaisesRegex(RuntimeError, "differ"):
            check_pipeline(mysql, pg)


class MartBuildTests(unittest.TestCase):
    def setUp(self):
        self.connection = MagicMock()
        self.cursor = self.connection.cursor.return_value.__enter__.return_value

    def test_incremental_batch_updates_state_after_facts(self):
        self.cursor.fetchone.return_value = (0,)
        self.cursor.fetchall.return_value = [(1,), (7,)]
        self.cursor.rowcount = 2
        self.assertEqual(build_batch(self.connection, 2), 2)
        self.assertEqual(self.cursor.execute.call_count, 6)
        self.assertEqual(self.cursor.execute.call_args.args[1], (7, "learning_events"))

    def test_fact_count_mismatch_rolls_back_state_update(self):
        self.cursor.fetchone.return_value = (0,)
        self.cursor.fetchall.return_value = [(1,), (7,)]
        self.cursor.rowcount = 1
        with self.assertRaisesRegex(RuntimeError, "fact row count"):
            build_batch(self.connection, 2)
        self.assertEqual(self.cursor.execute.call_count, 5)
        self.assertIsNotNone(self.connection.transaction.return_value.__exit__.call_args.args[0])

    def test_empty_batch_does_not_refresh_dimensions(self):
        self.cursor.fetchone.return_value = (7,)
        self.cursor.fetchall.return_value = []
        self.assertEqual(build_batch(self.connection), 0)
        self.assertEqual(self.cursor.execute.call_count, 2)


class MartQualityTests(unittest.TestCase):
    def setUp(self):
        self.connection = MagicMock()
        self.cursor = self.connection.cursor.return_value.__enter__.return_value

    def test_complete_dimensions_pass(self):
        self.cursor.fetchone.side_effect = [
            (1, 1), (1,), (1,), (0,), (0,), (0,), (1,),
        ]
        self.assertEqual(check_mart(self.connection), 1)

    def test_extra_learner_dimension_fails(self):
        self.cursor.fetchone.side_effect = [
            (1, 1), (1,), (1,), (0,), (1,),
        ]
        with self.assertRaisesRegex(RuntimeError, "learner dimension"):
            check_mart(self.connection)

    def test_extra_content_dimension_fails(self):
        self.cursor.fetchone.side_effect = [
            (1, 1), (1,), (1,), (0,), (0,), (1,),
        ]
        with self.assertRaisesRegex(RuntimeError, "content dimension"):
            check_mart(self.connection)


if __name__ == "__main__":
    unittest.main()
