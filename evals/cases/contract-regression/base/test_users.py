import unittest

from users import get_user


class GetUserTest(unittest.TestCase):
    def test_existing_shape(self) -> None:
        self.assertEqual(get_user(7), {"id": 7, "name": "Ada Lovelace"})


if __name__ == "__main__":
    unittest.main()
