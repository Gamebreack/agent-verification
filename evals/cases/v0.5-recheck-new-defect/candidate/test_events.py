import unittest

from events import process_events


def event(event_id: int, kind: str) -> dict:
    return {"id": event_id, "kind": kind, "payload": None}


class ProcessEventsTest(unittest.TestCase):
    def test_adjacent_redelivery_is_skipped(self) -> None:
        seen = []
        process_events([event(1, "created"), event(1, "created"), event(2, "paid")], seen.append)
        self.assertEqual([item["id"] for item in seen], [1, 2])

    def test_non_adjacent_redelivery_is_skipped(self) -> None:
        seen = []
        process_events([event(1, "created"), event(2, "paid"), event(1, "created")], seen.append)
        self.assertEqual([item["id"] for item in seen], [1, 2])


if __name__ == "__main__":
    unittest.main()
