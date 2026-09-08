import unittest

from builder import page


class PageV2Test(unittest.TestCase):
    def test_render_v2(self):
        result = page.render_v2()
        self.assertTrue(result["ok"])
        self.assertEqual(result["v"], 2)
