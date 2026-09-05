import unittest

from format_id import format_id


class FormatIdTest(unittest.TestCase):
    def test_formats_with_padding(self) -> None:
        self.assertEqual(format_id(7), "id-0007")

    def test_formats_larger_value(self) -> None:
        self.assertEqual(format_id(42), "id-0042")

    def test_formats_zero(self) -> None:
        self.assertEqual(format_id(0), "id-0000")


if __name__ == "__main__":
    unittest.main()