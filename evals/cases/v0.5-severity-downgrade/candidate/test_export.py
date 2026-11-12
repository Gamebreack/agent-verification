import os
import tempfile
import unittest

from export import export_report


class ExportReportTest(unittest.TestCase):
    def test_writes_header_and_rows_in_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "out.csv")
            export_report([("ana", 3), ("bo", 5)], path)
            with open(path, encoding="utf-8") as handle:
                self.assertEqual(handle.read(), "name,amount\nana,3\nbo,5\n")


if __name__ == "__main__":
    unittest.main()
