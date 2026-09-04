import unittest

from users import get_user


class GetUserTest(unittest.TestCase):
    def test_includes_email(self) -> None:
        user = get_user(7)
        self.assertEqual(user["display_name"], "Ada Lovelace")
        self.assertEqual(user["email"], "ada@example.com")


if __name__ == "__main__":
    unittest.main()
