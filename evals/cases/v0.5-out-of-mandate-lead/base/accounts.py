import threading


class Account:
    def __init__(self, account_id: str, balance: int) -> None:
        self.account_id = account_id
        self.balance = balance
        self.lock = threading.Lock()


def withdraw(account: Account, amount: int) -> int:
    with account.lock:
        if amount <= 0 or amount > account.balance:
            raise ValueError("invalid amount")
        account.balance -= amount
        return account.balance
