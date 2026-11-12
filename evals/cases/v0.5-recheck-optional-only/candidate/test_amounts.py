import os
import tempfile
import unittest

from amounts import parse_amount


class ParseAmountTest(unittest.TestCase):
    def test_parses_amounts_from_a_fixture_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "amounts_fixture.txt")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("7\n12.5\n12.50\n")
            with open(path, encoding="utf-8") as handle:
                parsed = [parse_amount(line) for line in handle]
        self.assertEqual(parsed, [700, 1250, 1250])

    def test_rejects_negative(self) -> None:
        with self.assertRaises(ValueError):
            parse_amount("-3")


if __name__ == "__main__":
    unittest.main()
