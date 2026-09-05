import unittest

from dedupe import dedupe


class DedupeTest(unittest.TestCase):
    def test_removes_duplicate_ids(self) -> None:
        events = [
            {"id": 1, "value": "a"},
            {"id": 2, "value": "b"},
            {"id": 1, "value": "a-again"},
        ]
        result = dedupe(events)
        self.assertEqual(len(result), 2)
        self.assertEqual([e["id"] for e in result], [1, 2])

    def test_empty_input_returns_empty(self) -> None:
        self.assertEqual(dedupe([]), [])

    def test_no_duplicates_passes_through(self) -> None:
        events = [{"id": 1}, {"id": 2}, {"id": 3}]
        result = dedupe(events)
        self.assertEqual([e["id"] for e in result], [1, 2, 3])


if __name__ == "__main__":
    unittest.main()