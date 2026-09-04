import unittest

from price import final_price


class FinalPriceTest(unittest.TestCase):
    def test_placeholder(self) -> None:
        with self.assertRaises(NotImplementedError):
            final_price(100, 0.1)


if __name__ == "__main__":
    unittest.main()
