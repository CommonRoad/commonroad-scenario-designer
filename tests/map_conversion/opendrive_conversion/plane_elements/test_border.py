import unittest
from crdesigner.map_conversion.opendrive.opendrive_conversion.plane_elements.border import Border
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadPlanView import PlanView
import numpy as np
import math


class TestBorder(unittest.TestCase):

    def test_initialize_border(self):
        offset = 0.0
        border = Border(offset)
        self.assertEqual(border.ref_offset, offset)

    def test_get_width_index(self):
        offset = 1.0
        border = Border(offset)
        border.width_coefficients = [5.0, 0.0, 0.0, 0.0]
        border.width_coefficient_offsets = [0.0, 1.0, 5.2, 7.8]

        s_pos = 0.0
        idx = border._get_width_index(s_pos, False)
        self.assertEqual(0, idx)

        s_pos = 1.0
        idx = border._get_width_index(s_pos, False)
        self.assertEqual(1.0, idx)

        s_pos = 5.4
        idx = border._get_width_index(s_pos, False)
        self.assertEqual(2, idx)

        s_pos = 10
        idx = border._get_width_index(s_pos, False)
        self.assertEqual(3, idx)

        s_pos = -1
        idx = border._get_width_index(s_pos, False)
        self.assertEqual(len(border.width_coefficient_offsets)-1, idx)

        s_pos = 5.4
        idx = border._get_width_index(s_pos, True)
        self.assertEqual(2, idx)

        s_pos = "test"
        self.assertRaises(TypeError, border._get_width_index, s_pos, False)

    def test_get_next_width_coeffs(self):
        border = Border(0.0)
        border.width_coefficients = [5.0, 0.8, 1.2, 0.052]
        border.width_coefficient_offsets = [0.0, 1.0, 5.2, 7.8]
        coeff = border.get_next_width_coeffs(5.4, False)
        self.assertEqual(1.2, coeff)

        coeff = border.get_next_width_coeffs(0.1, False)
        self.assertEqual(5.0, coeff)

        coeff = border.get_next_width_coeffs(10, True)
        self.assertEqual(0.052, coeff)

    def test_calc(self):
        view = PlanView(0.2, 0.3)
        # 45 degrees
        hdg = 0.785398
        view.add_line(0.0, hdg, 50)
        border = Border(0.0)
        border.width_coefficients = [5.0, 0.8, 1.2, 0.052]
        border.width_coefficient_offsets = [1.0, 1.0, 0.0, 0.0]
        border.reference = view
        s_pos = 25

        coord_line = np.array([np.cos(hdg) * s_pos, np.sin(hdg) * s_pos])

        ortho_at_s = hdg + np.pi / 2
        width_at_s = border.width_coefficients[2]
        offset_at_s = border.width_coefficient_offsets[2]
        distance = np.polynomial.polynomial.polyval(s_pos - offset_at_s, width_at_s)
        coord_border = coord_line + np.array(
                [distance * math.cos(ortho_at_s), distance * math.sin(ortho_at_s)]
        )

        coord, tang_angle, curv, max_geometry_length = border.calc(s_pos, 0.0, False, False, True)

        self.assertAlmostEqual(coord_border[0], coord[0])
        self.assertAlmostEqual(coord_border[1], coord[1])
