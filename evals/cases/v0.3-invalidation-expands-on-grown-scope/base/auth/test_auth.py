import unittest

from auth import check, tenants


class AuthTest(unittest.TestCase):
    def setUp(self):
        tenants.TENANTS.clear()

    def test_authorize_known_tenant(self):
        tenants.add_tenant("t1", "Acme")
        self.assertTrue(check.authorize("t1"))

    def test_reject_unknown_tenant(self):
        self.assertFalse(check.authorize("unknown"))
