import unittest

from accounts import Account, withdraw


class StubNotifier:
    def __init__(self) -> None:
        self.sent: list[tuple[str, int]] = []

    def send(self, account_id: str, amount: int) -> None:
        self.sent.append((account_id, amount))


class WithdrawTest(unittest.TestCase):
    def test_withdraw_reduces_balance_and_notifies_once(self) -> None:
        notifier = StubNotifier()
        self.assertEqual(withdraw(Account("a1", 10), 4, notifier), 6)
        self.assertEqual(notifier.sent, [("a1", 4)])

    def test_rejects_overdraft_without_notice(self) -> None:
        notifier = StubNotifier()
        with self.assertRaises(ValueError):
            withdraw(Account("a1", 10), 11, notifier)
        self.assertEqual(notifier.sent, [])


if __name__ == "__main__":
    unittest.main()
