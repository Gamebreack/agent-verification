import unittest
from unittest.mock import patch

import price


class FinalPriceTest(unittest.TestCase):
    @patch("price.final_price", return_value=110.0)
    def test_adds_tax(self, mocked_final_price) -> None:
        self.assertEqual(price.final_price(100, 0.1), 110.0)
        mocked_final_price.assert_called_once_with(100, 0.1)


if __name__ == "__main__":
    unittest.main()
