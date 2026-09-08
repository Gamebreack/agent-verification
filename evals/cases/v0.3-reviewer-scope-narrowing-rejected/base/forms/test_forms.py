import unittest

from forms import page, submission, validation


class FormCreationTest(unittest.TestCase):
    def test_renders_three_fields(self):
        self.assertEqual(len(page.render_form()["fields"]), 3)

    def test_submit_endpoint(self):
        self.assertEqual(page.render_form()["submit_endpoint"], "/api/forms")

    def test_email_validates_basic(self):
        self.assertTrue(validation.validate_email("user@example.com"))

    def test_message_validates(self):
        self.assertTrue(validation.validate_message("hello"))
        self.assertFalse(validation.validate_message(""))

    def test_submission_returns_id(self):
        self.assertIn("id", submission.submit_form({"x": 1}))
