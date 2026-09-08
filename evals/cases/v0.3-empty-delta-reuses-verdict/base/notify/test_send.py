import unittest

from notify import send


class SendTest(unittest.TestCase):
    def test_send_returns_delivered(self):
        result = send.send("hello")
        self.assertTrue(result["delivered"])
        self.assertEqual(result["message"], "hello")
