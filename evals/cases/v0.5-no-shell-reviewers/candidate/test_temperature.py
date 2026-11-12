import unittest

from temperature import celsius_to_fahrenheit, fahrenheit_to_celsius


class TemperatureTest(unittest.TestCase):
    def test_celsius_to_fahrenheit(self) -> None:
        self.assertEqual(celsius_to_fahrenheit(100), 212)

    def test_fahrenheit_to_celsius(self) -> None:
        self.assertEqual(fahrenheit_to_celsius(212), 100)
        self.assertAlmostEqual(fahrenheit_to_celsius(0), -17.7777777, places=5)


if __name__ == "__main__":
    unittest.main()
