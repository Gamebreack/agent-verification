import unittest

from status import display_status


class DisplayStatusTest(unittest.TestCase):
    def test_snake_case(self) -> None:
        self.assertEqual(display_status("in_progress"), "In Progress")

    def test_single_word(self) -> None:
        self.assertEqual(display_status("pending"), "Pending")


if __name__ == "__main__":
    unittest.main()
