from typing import List, Tuple
import unittest

from app.utilities import utils
from app.utilities.typing import Point

class UtilsTests(unittest.TestCase):
    def test_average_pos(self):
        from app.utilities.utils import average_pos
        self.assertEqual(average_pos([(0, 0), (1, 1), (2, 2)]), (1, 1))
        self.assertEqual(average_pos([(0, 0), (1, 1), (3, 3)]), (4/3, 4/3))
        self.assertEqual(average_pos([(0, 0), (1, 1), (3, 3), (4, 4)]), (2, 2))

    def test_smart_farthest_away_pos(self):
        from app.utilities.utils import smart_farthest_away_pos, calculate_distance

        def generate_enemy_pos(unit_pos: Point, pos_list: List[Point]) -> List[Tuple[Point, int]]:
            return [(pos, calculate_distance(unit_pos, pos)) for pos in pos_list]
        unit_pos = (0, 0)
        valid_moves = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        def assert_pos(enemy_pos, expected):
            enemy_pos = generate_enemy_pos(unit_pos, enemy_pos)
            self.assertEqual(smart_farthest_away_pos(unit_pos, valid_moves, enemy_pos), expected)

        assert_pos([(1, 1)], (-1, -1))
        assert_pos([(1, 1), (1, 0), (1, -1), (1, -2)], (-1, 1))

if __name__ == '__main__':
    unittest.main()
