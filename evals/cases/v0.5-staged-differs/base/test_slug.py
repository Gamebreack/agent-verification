import unittest

from slug import slugify


class SlugifyTest(unittest.TestCase):
    def test_simple_title(self) -> None:
        self.assertEqual(slugify(" Hello World "), "hello-world")


if __name__ == "__main__":
    unittest.main()
