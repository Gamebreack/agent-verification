import unittest

from limits import is_valid_page_size


class PageSizeBoundaryTest(unittest.TestCase):
    def test_limit_is_inclusive(self) -> None:
        self.assertTrue(is_valid_page_size(100))
        self.assertFalse(is_valid_page_size(101))


if __name__ == "__main__":
    unittest.main()
