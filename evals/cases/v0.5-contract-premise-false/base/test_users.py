import unittest

from users import display_name


class DisplayNameTest(unittest.TestCase):
    def test_joins_names(self) -> None:
        self.assertEqual(display_name(" Ada ", "Lovelace"), "Ada Lovelace")


if __name__ == "__main__":
    unittest.main()
