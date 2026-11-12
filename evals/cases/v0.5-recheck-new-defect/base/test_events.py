import unittest

from events import process_events


class ProcessEventsTest(unittest.TestCase):
    def test_handles_each_event(self) -> None:
        seen = []
        process_events([{"id": 1, "kind": "a", "payload": None}], seen.append)
        self.assertEqual([event["id"] for event in seen], [1])


if __name__ == "__main__":
    unittest.main()
