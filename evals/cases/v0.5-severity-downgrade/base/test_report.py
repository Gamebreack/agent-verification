import unittest

from report import render_csv


class RenderCsvTest(unittest.TestCase):
    def test_header_and_rows(self) -> None:
        self.assertEqual(render_csv([("ana", 3)]), "name,amount\nana,3\n")


if __name__ == "__main__":
    unittest.main()
