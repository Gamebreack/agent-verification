import unittest

from cart import add_item


class AddItemTest(unittest.TestCase):
    def test_adds_quantity(self) -> None:
        self.assertEqual(add_item({"a": 1}, "a", 2), {"a": 3})

    def test_rejects_negative_quantity(self) -> None:
        with self.assertRaises(ValueError):
            add_item({}, "a", -1)


if __name__ == "__main__":
    unittest.main()
