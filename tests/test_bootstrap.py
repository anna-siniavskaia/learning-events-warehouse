import stat
import tempfile
import unittest
from pathlib import Path

from scripts.bootstrap import ensure_local_env


class BootstrapTests(unittest.TestCase):
    def test_creates_private_credentials_once(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / ".env"
            self.assertTrue(ensure_local_env(path))
            first = path.read_text(encoding="utf-8")
            values = dict(line.split("=", 1) for line in first.strip().splitlines())
            self.assertEqual(set(values), {
                "MYSQL_PASSWORD", "MYSQL_ROOT_PASSWORD", "POSTGRES_PASSWORD",
            })
            self.assertEqual(len(set(values.values())), 3)
            self.assertTrue(all(len(value) >= 24 for value in values.values()))
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertFalse(ensure_local_env(path))
            self.assertEqual(path.read_text(encoding="utf-8"), first)

    def test_rejects_example_passwords(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / ".env"
            path.write_text("MYSQL_PASSWORD=replace-with-local-password\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "example passwords"):
                ensure_local_env(path)

    def test_rejects_incomplete_existing_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / ".env"
            path.write_text("MYSQL_PASSWORD=local-only\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "three nonempty"):
                ensure_local_env(path)


if __name__ == "__main__":
    unittest.main()
