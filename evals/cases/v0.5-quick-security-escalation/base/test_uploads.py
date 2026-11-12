import unittest

from uploads import UPLOAD_DIR, upload_path


class UploadPathTest(unittest.TestCase):
    def test_joins_filename(self) -> None:
        self.assertEqual(upload_path("a.txt"), UPLOAD_DIR / "a.txt")


if __name__ == "__main__":
    unittest.main()
