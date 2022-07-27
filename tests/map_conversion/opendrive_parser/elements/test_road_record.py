import unittest
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.road_record import *


class TestRoadRecord(unittest.TestCase):
    def test_initialize_road_record(self):
        a, b, c, d = 2.0, 3.0, 5.0, 1.0
        start_pos = 0

        road_record = RoadRecord(a, b, c, d, start_pos=start_pos)

        self.assertEqual(road_record.start_pos, start_pos)
        self.assertEqual([a, b, c, d], road_record.polynomial_coefficients)


if __name__ == '__main__':
    unittest.main()
