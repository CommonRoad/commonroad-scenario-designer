import unittest
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadLateralProfile import *

class TestLateralProfile(unittest.TestCase):
    def test_initialize_shape(self):
        a, b, c, d = 2.0, 3.0, 5.0, 1.0
        s_value = 3
        t_value = 1
        shape = Shape(a, b, c, d, start_pos=s_value, start_pos_t=t_value)

        self.assertEqual([a, b, c, d], shape.polynomial_coefficients)
        self.assertEqual(s_value, shape.start_pos)
        self.assertEqual(t_value, shape.start_pos_t)

    def test_crossfall(self):
        a, b, c, d = 2.0, 3.0, 5.0, 1.0
        s_value = 3
        crossfall = Crossfall(a, b, c, d, start_pos=s_value, side="left")

        self.assertEqual([a, b, c, d], crossfall.polynomial_coefficients)
        self.assertEqual(s_value, crossfall.start_pos)
        with self.assertRaises(TypeError):
            crossfall.side = "wrong_attribute"
            crossfall.side = 4
            crossfall.side = None
        for value in ["left", "right", "both"]:
            crossfall.side = value
            self.assertEqual(value, crossfall.side)

    def test_initialize_lateral_profile(self):
        a, b, c, d = 2.0, 3.0, 5.0, 1.0
        se1 = Superelevation(a, b, c, d, start_pos=3)
        se2 = Superelevation(a, b, c, d, start_pos=1)
        se3 = Superelevation(a, b, c, d, start_pos=2)
        cf1 = Crossfall(a, b, c, d, start_pos=5, side="left")
        cf2 = Crossfall(a, b, c, d, start_pos=4, side="left")
        cf3 = Crossfall(a, b, c, d, start_pos=1, side="left")
        s1 = Shape(a, b, c, d, start_pos=4, start_pos_t=5)
        s2 = Shape(a, b, c, d, start_pos=4, start_pos_t=3)
        s3 = Shape(a, b, c, d, start_pos=2, start_pos_t=5)
        lp = LateralProfile()
        lp.superelevations = [se1, se2, se3]
        lp.crossfalls = [cf1, cf2, cf3]
        lp.shapes = [s1, s2, s3]

        self.assertEqual([se2, se3, se1], lp.superelevations)
        self.assertEqual([cf3, cf2, cf1], lp.crossfalls)
        self.assertEqual([s3, s2, s1], lp.shapes)
        with self.assertRaises(TypeError):
            lp.shapes = s1
            lp.shapes = [1]
            lp.crossfalls = cf3
            lp.crossfalls = ["test", 2]
            lp.superelevations = se2
            lp.superelevations = [se1, "test"]


if __name__ == "__main__":
    unittest.main()
