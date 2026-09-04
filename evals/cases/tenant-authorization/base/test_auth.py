import unittest

from auth import can_view


class CanViewTest(unittest.TestCase):
    def test_placeholder(self) -> None:
        with self.assertRaises(NotImplementedError):
            can_view("tenant-a", "tenant-a")


if __name__ == "__main__":
    unittest.main()
