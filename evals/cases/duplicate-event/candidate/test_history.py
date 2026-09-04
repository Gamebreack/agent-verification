import unittest

from history import HistoryStore


class HistoryStoreTest(unittest.TestCase):
    def test_records_event(self) -> None:
        store = HistoryStore()
        store.record("evt-1", 10)
        self.assertEqual(store.entries, [("evt-1", 10)])


if __name__ == "__main__":
    unittest.main()
