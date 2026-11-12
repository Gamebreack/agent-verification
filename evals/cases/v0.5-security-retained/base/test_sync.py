import os
import tempfile
import unittest

from sync import load_cache, save_cache, should_retry


class SyncTest(unittest.TestCase):
    def test_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "cache.json")
            save_cache(path, {"k": "v"})
            self.assertEqual(load_cache(path), {"k": "v"})

    def test_retry_limit(self) -> None:
        self.assertTrue(should_retry(2))
        self.assertFalse(should_retry(3))


if __name__ == "__main__":
    unittest.main()
