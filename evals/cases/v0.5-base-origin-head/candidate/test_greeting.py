import unittest

from greeting import greet


class GreetTest(unittest.TestCase):
    def test_greets(self) -> None:
        self.assertEqual(greet("Ada"), "Hello, Ada!")

    def test_strips_whitespace(self) -> None:
        self.assertEqual(greet("  Ada \n"), "Hello, Ada!")


if __name__ == "__main__":
    unittest.main()
