import unittest

from profile import format_profile


class FormatProfileTest(unittest.TestCase):
    def test_trims_first_name(self) -> None:
        self.assertEqual(format_profile("  Ada  ", "Lovelace"), "Ada")


if __name__ == "__main__":
    unittest.main()
