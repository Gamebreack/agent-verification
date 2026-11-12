import unittest

from window import sliding_windows


class SlidingWindowsTest(unittest.TestCase):
    def test_first_window(self) -> None:
        self.assertEqual(sliding_windows([1, 2, 3, 4], 2)[0], [1, 2])

    def test_rejects_non_positive_size(self) -> None:
        self.assertEqual(sliding_windows([1, 2], 0), [])


if __name__ == "__main__":
    unittest.main()
