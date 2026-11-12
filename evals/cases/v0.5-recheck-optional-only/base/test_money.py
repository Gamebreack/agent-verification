import unittest

from money import format_cents


class FormatCentsTest(unittest.TestCase):
    def test_formats(self) -> None:
        self.assertEqual(format_cents(1250), "12.50")


if __name__ == "__main__":
    unittest.main()
