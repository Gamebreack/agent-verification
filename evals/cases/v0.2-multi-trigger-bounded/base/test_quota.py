import unittest

from quota import allocate


class AllocateTest(unittest.TestCase):
    def test_placeholder(self) -> None:
        with self.assertRaises(NotImplementedError):
            allocate("t1", 1, 0, 10)


if __name__ == "__main__":
    unittest.main()