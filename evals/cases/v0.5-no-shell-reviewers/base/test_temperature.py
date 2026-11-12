import unittest

from temperature import celsius_to_fahrenheit


class TemperatureTest(unittest.TestCase):
    def test_celsius_to_fahrenheit(self) -> None:
        self.assertEqual(celsius_to_fahrenheit(100), 212)


if __name__ == "__main__":
    unittest.main()
