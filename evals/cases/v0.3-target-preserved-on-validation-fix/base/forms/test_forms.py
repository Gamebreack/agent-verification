import unittest

from forms import api, page, submission, validation


class FormCreationTest(unittest.TestCase):
    def test_renders_three_fields(self):
        form = page.render_form()
        self.assertEqual(len(form["fields"]), 3)

    def test_submit_endpoint(self):
        self.assertEqual(page.render_form()["submit_endpoint"], "/api/forms")

    def test_email_validates_basic(self):
        self.assertTrue(validation.validate_email("user@example.com"))
        self.assertFalse(validation.validate_email("no-at-sign"))

    def test_message_must_be_non_empty(self):
        self.assertFalse(validation.validate_message(""))
        self.assertFalse(validation.validate_message("   "))
        self.assertTrue(validation.validate_message("hello"))

    def test_submission_returns_id(self):
        self.assertIn("id", submission.submit_form({"x": 1}))

    def test_api_endpoint_preserved(self):
        self.assertTrue(api.handle_forms_post({"a": 1})["saved"])
