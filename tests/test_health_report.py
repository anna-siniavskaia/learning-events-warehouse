import unittest
from decimal import Decimal
from unittest.mock import MagicMock

from src.health_report import collect_health


class HealthReportTests(unittest.TestCase):
    def connections(self, source, warehouse_results):
        mysql = MagicMock()
        mysql.cursor.return_value.__enter__.return_value.fetchone.return_value = source
        postgres = MagicMock()
        postgres.cursor.return_value.__enter__.return_value.fetchone.side_effect = warehouse_results
        return mysql, postgres

    def test_healthy_snapshot_has_zero_lag(self):
        mysql, postgres = self.connections(
            (110, Decimal("110")),
            [(110, 110), (110, 110), (110,), (110,)],
        )
        report = collect_health(mysql, postgres)
        self.assertEqual(report["status"], "healthy")
        self.assertTrue(report["healthy"])
        self.assertEqual(report["ingestion_lag"], 0)
        self.assertEqual(report["mart_lag"], 0)

    def test_pending_source_and_mart_rows_are_degraded(self):
        mysql, postgres = self.connections(
            (110, 110),
            [(105, 105), (100, 100), (105,), (100,)],
        )
        report = collect_health(mysql, postgres)
        self.assertEqual(report["status"], "degraded")
        self.assertFalse(report["healthy"])
        self.assertEqual(report["ingestion_lag"], 5)
        self.assertEqual(report["mart_lag"], 5)

    def test_missing_watermark_fails_explicitly(self):
        mysql, postgres = self.connections(
            (0, 0),
            [(0, 0), (0, 0), None, (0,)],
        )
        with self.assertRaisesRegex(RuntimeError, "watermark is missing"):
            collect_health(mysql, postgres)


if __name__ == "__main__":
    unittest.main()
