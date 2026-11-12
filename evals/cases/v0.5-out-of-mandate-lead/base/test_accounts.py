import unittest

from accounts import Account, withdraw


class WithdrawTest(unittest.TestCase):
    def test_withdraw_reduces_balance(self) -> None:
        self.assertEqual(withdraw(Account("a1", 10), 4), 6)

    def test_rejects_overdraft(self) -> None:
        with self.assertRaises(ValueError):
            withdraw(Account("a1", 10), 11)


if __name__ == "__main__":
    unittest.main()
