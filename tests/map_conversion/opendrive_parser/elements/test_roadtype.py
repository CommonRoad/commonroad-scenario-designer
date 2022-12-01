import unittest
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadtype import *


class TestRoadType(unittest.TestCase):
    def test_initialize_speed(self):
        s_max = "50"
        unit = "km/h"
        speed = Speed(max_speed=s_max, unit=unit)

        self.assertEqual("50", speed.max)
        self.assertEqual("km/h", speed.unit)
        speed.max = "30.5"
        self.assertEqual("30.5", speed.max)
        for value in ["no limit", "undefined"]:
            speed.max = value
            self.assertEqual(value, speed.max)
        with self.assertRaises(AttributeError):
            speed.max = "test"
            speed.max = None
        speed.unit = "mph"
        self.assertEqual("mph", speed.unit)
        with self.assertRaises(AttributeError):
            speed.unit = 2
            speed.unit = "m/h"
            speed.unit = None

    def test_initialize_road_type(self):
        s_pos = "1.3"
        types = RoadType.allowedTypes
        speed = Speed(max_speed="50", unit="km/h")
        road_type = RoadType(s_pos=s_pos, use_type=types[0], speed=speed)

        self.assertEqual(1.3, road_type.start_pos)
        self.assertEqual(types[0], road_type.use_type)
        self.assertEqual(speed, road_type.speed)
        road_type.start_pos = "5"
        self.assertEqual(5, road_type.start_pos)
        for r_type in types:
            road_type.use_type = r_type
            self.assertEqual(r_type, road_type.use_type)
        with self.assertRaises(AttributeError):
            road_type.use_type = "test"
            road_type.use_type = 3
            road_type.use_type = None
        with self.assertRaises(TypeError):
            road_type.speed = 3
            road_type.speed = "not defined"
        road_type.speed = None
        self.assertEqual(None, road_type.speed)


if __name__ == '__main__':
    unittest.main()
