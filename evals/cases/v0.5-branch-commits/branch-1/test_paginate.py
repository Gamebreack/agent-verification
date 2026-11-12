import unittest

from paginate import paginate


class PaginateTest(unittest.TestCase):
    def test_full_page_has_page_size_items(self) -> None:
        self.assertEqual(len(paginate(list(range(30)), 1, 10)), 10)


if __name__ == "__main__":
    unittest.main()
