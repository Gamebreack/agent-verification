import unittest

from quota import allocate


class AllocateTest(unittest.TestCase):
    def test_grants_within_quota(self) -> None:
        result = allocate("t1", 3, 5, 10)
        self.assertEqual(result["granted"], 3)
        self.assertEqual(result["reason"], "ok")
        self.assertEqual(result["remaining"], 2)

    def test_denies_over_quota(self) -> None:
        result = allocate("t1", 8, 5, 10)
        self.assertEqual(result["granted"], 0)
        self.assertEqual(result["reason"], "over_quota")

    def test_denies_missing_tenant(self) -> None:
        result = allocate("", 1, 0, 10)
        self.assertEqual(result["granted"], 0)
        self.assertEqual(result["reason"], "unauthorized")

    def test_response_shape_is_stable(self) -> None:
        result = allocate("t1", 1, 0, 10)
        self.assertEqual(set(result.keys()), {"granted", "reason", "remaining"})


if __name__ == "__main__":
    unittest.main()