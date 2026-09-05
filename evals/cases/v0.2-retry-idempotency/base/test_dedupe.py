import unittest

from dedupe import dedupe


class DedupeTest(unittest.TestCase):
    def test_placeholder(self) -> None:
        with self.assertRaises(NotImplementedError):
            dedupe([])


if __name__ == "__main__":
    unittest.main()