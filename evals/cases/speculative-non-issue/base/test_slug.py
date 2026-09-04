import unittest

from slug import slugify


class SlugifyTest(unittest.TestCase):
    def test_normalizes_case_and_whitespace(self) -> None:
        self.assertEqual(slugify("  Hello  "), "hello")


if __name__ == "__main__":
    unittest.main()
