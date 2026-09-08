import unittest

from forms import page


class PageTest(unittest.TestCase):
    def test_render(self):
        self.assertTrue(page.render()["ok"])
