import unittest

from slots import within_slot_limit


class SlotLimitTest(unittest.TestCase):
    def test_below_limit(self) -> None:
        self.assertTrue(within_slot_limit(2, 3))

    def test_above_limit(self) -> None:
        self.assertFalse(within_slot_limit(4, 3))

    def test_rejects_negative(self) -> None:
        with self.assertRaises(ValueError):
            within_slot_limit(-1, 3)


if __name__ == "__main__":
    unittest.main()
