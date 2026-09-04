import unittest

from history import HistoryStore


class HistoryStoreTest(unittest.TestCase):
    def test_placeholder(self) -> None:
        store = HistoryStore()
        with self.assertRaises(NotImplementedError):
            store.record("evt-1", 10)


if __name__ == "__main__":
    unittest.main()
