import unittest

from slots import within_slot_limit


class SlotLimitTest(unittest.TestCase):
    def test_placeholder(self) -> None:
        with self.assertRaises(NotImplementedError):
            within_slot_limit(0, 1)


if __name__ == "__main__":
    unittest.main()
