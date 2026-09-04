import unittest

from profile import format_profile


class FormatProfileTest(unittest.TestCase):
    def test_placeholder(self) -> None:
        with self.assertRaises(NotImplementedError):
            format_profile("Ada", "Lovelace")


if __name__ == "__main__":
    unittest.main()
