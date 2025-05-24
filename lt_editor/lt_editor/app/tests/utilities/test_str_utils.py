import unittest

class StrUtilsTests(unittest.TestCase):
    def test_get_prefix(self):
        from app.utilities.str_utils import get_prefix
        self.assertEqual(get_prefix('image0.png'), 'image')
        self.assertEqual(get_prefix('image1.png'), 'image')
        self.assertEqual(get_prefix('image10.png'), 'image')
        self.assertEqual(get_prefix('image.png'), 'image')
        self.assertEqual(get_prefix('image.png.png'), 'image')

if __name__ == '__main__':
    unittest.main()
