import unittest

from users import display_name, normalize_email


class DisplayNameTest(unittest.TestCase):
    def test_joins_names(self) -> None:
        self.assertEqual(display_name(" Ada ", "Lovelace"), "Ada Lovelace")


class NormalizeEmailTest(unittest.TestCase):
    def test_lowercases_the_domain_only(self) -> None:
        self.assertEqual(normalize_email("Ada.L@Example.COM"), "Ada.L@example.com")


if __name__ == "__main__":
    unittest.main()
