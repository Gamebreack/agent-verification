import unittest

from rate import allow_request


class BurstBoundaryTest(unittest.TestCase):
    def test_exactly_burst_is_allowed(self) -> None:
        self.assertTrue(allow_request(10, 10))
        self.assertFalse(allow_request(11, 10))


if __name__ == "__main__":
    unittest.main()
