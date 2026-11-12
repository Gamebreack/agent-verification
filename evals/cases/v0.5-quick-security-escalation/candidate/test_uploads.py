import unittest

from uploads import UPLOAD_DIR, upload_path


class UploadPathTest(unittest.TestCase):
    def test_joins_filename(self) -> None:
        self.assertEqual(upload_path("a.txt"), UPLOAD_DIR / "a.txt")
        self.assertEqual(upload_path("..hidden"), UPLOAD_DIR / "..hidden")

    def test_rejects_unsafe_names(self) -> None:
        for name in ("", ".", "..", "../etc/passwd", "a/b", "a\\b", "a\0b"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                upload_path(name)


if __name__ == "__main__":
    unittest.main()
