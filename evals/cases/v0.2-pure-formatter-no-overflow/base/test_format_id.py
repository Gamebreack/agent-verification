import unittest

from format_id import format_id


class FormatIdTest(unittest.TestCase):
    def test_placeholder(self) -> None:
        with self.assertRaises(NotImplementedError):
            format_id(1)


if __name__ == "__main__":
    unittest.main()