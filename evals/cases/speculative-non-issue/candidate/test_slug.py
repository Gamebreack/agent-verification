import unittest

from slug import slugify


class SlugifyTest(unittest.TestCase):
    def test_normalizes_label(self) -> None:
        self.assertEqual(slugify("  Hello World  "), "hello-world")

    def test_preserves_single_word_behavior(self) -> None:
        self.assertEqual(slugify("  Status  "), "status")


if __name__ == "__main__":
    unittest.main()
