import unittest

import config


class ConfigTest(unittest.TestCase):
    def test_default_page_size(self) -> None:
        self.assertEqual(config.DEFAULT_PAGE_SIZE, 50)


if __name__ == "__main__":
    unittest.main()
