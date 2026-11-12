import unittest

from discount import apply_discount


class DiscountTest(unittest.TestCase):
    def test_ten_percent(self) -> None:
        self.assertEqual(apply_discount(1000, 10), 900)


if __name__ == "__main__":
    unittest.main()
