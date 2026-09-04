import unittest

from webhook import verify_webhook


class VerifyWebhookTest(unittest.TestCase):
    def test_placeholder(self) -> None:
        with self.assertRaises(NotImplementedError):
            verify_webhook(b"payload", "signature", b"secret")


if __name__ == "__main__":
    unittest.main()
