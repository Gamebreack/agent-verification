import unittest

from slug import slugify


class SlugifyTest(unittest.TestCase):
    def test_simple_title(self) -> None:
        self.assertEqual(slugify(" Hello World "), "hello-world")

    def test_keeps_digits_and_collapses_separators(self) -> None:
        self.assertEqual(slugify("  Release 2.0 Notes! "), "release-2-0-notes")


if __name__ == "__main__":
    unittest.main()
