import unittest
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadElevationProfile import *


class TestRoadElevationProfile(unittest.TestCase):
    def test_initialize_elevation_record(self):
        a, b, c, d = 2.0, 3.0, 5.0, 1.0
        start_pos = 0

        elevation = ElevationRecord(a, b, c, d, start_pos=start_pos)

        self.assertEqual(elevation.start_pos, start_pos)
        self.assertEqual([a, b, c, d], elevation.polynomial_coefficients)

    def test_initialize_elevation_profile(self):
        a, b, c, d = 2.0, 3.0, 5.0, 1.0
        start_pos = 0

        elevation1 = ElevationRecord(a, b, c, d, start_pos=start_pos)
        elevation2 = ElevationRecord(b, c, d, a, start_pos=1)
        elevation3 = ElevationRecord(c, a, c, a, start_pos=3)

        elevation_profile = ElevationProfile()
        elevation_profile.elevations.append(elevation3)
        elevation_profile.elevations.append(elevation1)
        elevation_profile.elevations.append(elevation2)

        self.assertTrue(elevation1 in elevation_profile.elevations)
        self.assertTrue(elevation3 in elevation_profile.elevations)
        self.assertTrue(elevation2 in elevation_profile.elevations)


if __name__ == '__main__':
    unittest.main()
