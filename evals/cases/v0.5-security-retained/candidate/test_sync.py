import json
import os
import tempfile
import unittest
from types import SimpleNamespace

from sync import MAX_ATTEMPTS, clear_cache, load_cache, save_cache, should_retry


class SyncTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = os.path.join(self._tmp.name, "cache.json")

    def test_round_trip_writes_version_2(self) -> None:
        save_cache(self.path, {"k": "v"})
        with open(self.path, encoding="utf-8") as handle:
            self.assertEqual(json.load(handle), {"version": 2, "entries": {"k": "v"}})
        self.assertEqual(load_cache(self.path), {"k": "v"})

    def test_old_format_and_missing_files_are_cache_misses(self) -> None:
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump({"k": "v"}, handle)
        self.assertEqual(load_cache(self.path), {})
        self.assertEqual(load_cache(self.path + ".missing"), {})

    def test_retry_boundary(self) -> None:
        self.assertEqual(MAX_ATTEMPTS, 5)
        self.assertTrue(should_retry(4))
        self.assertFalse(should_retry(5))

    def test_only_admins_clear_the_cache(self) -> None:
        save_cache(self.path, {"k": "v"})
        with self.assertRaises(PermissionError):
            clear_cache(SimpleNamespace(is_admin=False), self.path)
        self.assertTrue(os.path.exists(self.path))
        clear_cache(SimpleNamespace(is_admin=True), self.path)
        self.assertFalse(os.path.exists(self.path))


if __name__ == "__main__":
    unittest.main()
