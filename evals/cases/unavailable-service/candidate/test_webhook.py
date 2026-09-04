import hashlib
import hmac
import unittest

from webhook import verify_webhook


class VerifyWebhookTest(unittest.TestCase):
    def test_accepts_matching_local_hmac(self) -> None:
        payload = b"payload"
        secret = b"local-secret"
        signature = hmac.new(secret, payload, hashlib.sha256).hexdigest()
        self.assertTrue(verify_webhook(payload, signature, secret))

    def test_rejects_invalid_signature(self) -> None:
        self.assertFalse(verify_webhook(b"payload", "invalid", b"local-secret"))


if __name__ == "__main__":
    unittest.main()
