import unittest

from rate import allow_request


class AllowRequestTest(unittest.TestCase):
    def test_under_and_over_the_limit(self) -> None:
        self.assertTrue(allow_request(3, 10))
        self.assertFalse(allow_request(11, 10))


if __name__ == "__main__":
    unittest.main()
