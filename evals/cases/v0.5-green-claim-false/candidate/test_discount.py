import unittest

from discount import apply_discount


class DiscountTest(unittest.TestCase):
    def test_ten_percent(self) -> None:
        self.assertEqual(apply_discount(1000, 10), 900)

    def test_full_discount_is_free(self) -> None:
        self.assertEqual(apply_discount(500, 100), 0)

    def test_rejects_out_of_range_percent(self) -> None:
        for percent in (-1, 101):
            with self.subTest(percent=percent), self.assertRaises(ValueError):
                apply_discount(500, percent)


if __name__ == "__main__":
    unittest.main()
