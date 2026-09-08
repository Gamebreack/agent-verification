import unittest

from auth import audit, check, tenants


class AuthTest(unittest.TestCase):
    def setUp(self):
        tenants.TENANTS.clear()

    def test_authorize_known_tenant(self):
        tenants.add_tenant("t1", "Acme")
        self.assertTrue(check.authorize("t1"))

    def test_reject_unknown_tenant(self):
        self.assertFalse(check.authorize("unknown"))

    def test_list_tenants(self):
        tenants.add_tenant("t2", "Beta")
        result = audit.list_tenants()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "t2")
