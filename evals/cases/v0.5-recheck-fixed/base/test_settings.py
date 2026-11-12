import unittest

from settings import client_settings


class SettingsTest(unittest.TestCase):
    def test_timeout(self) -> None:
        self.assertEqual(client_settings()["timeout"], 30)


if __name__ == "__main__":
    unittest.main()
