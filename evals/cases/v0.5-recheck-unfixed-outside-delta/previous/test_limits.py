import unittest

from limits import is_valid_page_size


class PageSizeTest(unittest.TestCase):
    def test_typical_sizes(self) -> None:
        self.assertTrue(is_valid_page_size(10))
        self.assertFalse(is_valid_page_size(0))


if __name__ == "__main__":
    unittest.main()
