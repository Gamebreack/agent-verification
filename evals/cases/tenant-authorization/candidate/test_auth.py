import unittest

from auth import can_view


class CanViewTest(unittest.TestCase):
    def test_same_tenant_allowed(self) -> None:
        self.assertTrue(can_view("tenant-a", "tenant-a"))

    def test_missing_tenant_denied(self) -> None:
        self.assertFalse(can_view(None, "tenant-a"))


if __name__ == "__main__":
    unittest.main()
