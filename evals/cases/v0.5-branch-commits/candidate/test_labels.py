import unittest

from labels import plural_label


class PluralLabelTest(unittest.TestCase):
    def test_many(self) -> None:
        self.assertEqual(plural_label(3, "item"), "3 items")

    def test_one(self) -> None:
        self.assertEqual(plural_label(1, "item"), "1 item")


if __name__ == "__main__":
    unittest.main()
