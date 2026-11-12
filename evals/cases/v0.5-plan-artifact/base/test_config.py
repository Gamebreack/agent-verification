import json
import os
import tempfile
import unittest

import config


class LoadTest(unittest.TestCase):
    def test_merges_over_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "config.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump({"timeout": 5}, handle)
            self.assertEqual(config.load(path), {"timeout": 5, "retries": 3})


if __name__ == "__main__":
    unittest.main()
