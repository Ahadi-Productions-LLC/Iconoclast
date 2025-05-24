import unittest

from app.utilities.algorithms.interpolation import tcubic_easing

class InterpTests(unittest.TestCase):
    def test_interpolations_are_clamped(self):
        a = (0, 0)
        b = (1, 1)
        self.assertEqual(tcubic_easing(a, b, -1), (0, 0))
        self.assertEqual(tcubic_easing(a, b, 0), (0, 0))
        self.assertEqual(tcubic_easing(a, b, 1), (1, 1))
        self.assertEqual(tcubic_easing(a, b, 2), (1, 1))

if __name__ == '__main__':
    unittest.main()
