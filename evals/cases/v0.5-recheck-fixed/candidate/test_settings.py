import unittest

from settings import client_settings


class SettingsTest(unittest.TestCase):
    def test_settings(self) -> None:
        self.assertEqual(client_settings(), {"timeout": 30, "burst": 10})


if __name__ == "__main__":
    unittest.main()
