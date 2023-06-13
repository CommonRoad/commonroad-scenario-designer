import unittest
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.geometry import *
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.eulerspiral import EulerSpiral
import numpy as np


class TestGeometry(unittest.TestCase):
    def test_initialize_line(self):
        start_position = np.array([2, 5])
        length = 4
        heading = 1.2

        line = Line(start_position=start_position, heading=heading, length=length)

        np.testing.assert_equal(start_position, line.start_position)
        self.assertEqual(length, line.length)
        self.assertEqual(heading, line.heading)

    def test_initialize_arc(self):
        start_position = np.array([2, 5])
        length = 4
        heading = 1.2
        curvature = 1

        arc = Arc(start_position=start_position, heading=heading, length=length, curvature=curvature)

        np.testing.assert_equal(start_position, arc.start_position)
        self.assertEqual(length, arc.length)
        self.assertEqual(heading, arc.heading)
        self.assertEqual(curvature, arc.curvature)

    def test_initialize_spiral(self):
        start_position = np.array([2, 5])
        length = 4
        heading = 1.2
        curv_start = 1
        curv_end = 2
        true_spiral = EulerSpiral.create_from_length_and_curvature(length, curv_start, curv_end)

        spiral = Spiral(start_position=start_position, heading=heading, length=length, curv_start=curv_start,
                        curv_end=curv_end)

        np.testing.assert_equal(start_position, spiral.start_position)
        self.assertEqual(length, spiral.length)
        self.assertEqual(heading, spiral.heading)
        self.assertEqual(curv_start, spiral._curv_start)
        self.assertEqual(curv_end, spiral._curv_end)
        self.assertEqual(true_spiral._gamma, spiral._spiral._gamma)

    def test_initialize_poly3(self):
        start_position = np.array([2, 5])
        length = 4
        heading = 1.2
        a = 2
        b = 3
        c = 1
        d = 5

        poly3 = Poly3(start_position=start_position, heading=heading, length=length,
                      a=a, b=b, c=c, d=d)

        np.testing.assert_equal(start_position, poly3.start_position)
        self.assertEqual(heading, poly3.heading)
        self.assertEqual(length, poly3.length)
        np.testing.assert_equal([a, b, c, d], poly3.coeffs)
        np.testing.assert_equal([b, 2*c, 3*d], poly3.d_coeffs)
        np.testing.assert_equal([2*c, 6*d], poly3.d2_coeffs)

    def test_initialize_paramPoly3(self):
        start_position = np.array([2, 5])
        length = 4
        heading = 1.2
        aU = 4
        bU = 3
        cU = 2
        dU = 1
        aV = 2
        bV = 4
        cV = 5
        dV = 6
        pRange = 4

        param_poly3 = ParamPoly3(start_position=start_position, heading=heading, length=length,
                                aU=aU, bU=bU, cU=cU, dU=dU, aV=aV, bV=bV, cV=cV, dV=dV, pRange=pRange)

        np.testing.assert_equal(start_position, param_poly3.start_position)
        self.assertEqual(dV, param_poly3.curvature_derivative_max)
        self.assertEqual(dU, param_poly3.curvature_derivative_min)
        self.assertEqual(heading, param_poly3.heading)
        self.assertEqual(length, param_poly3.length)
        np.testing.assert_equal([aU, bU, cU, dU], param_poly3.coeffs_u)
        np.testing.assert_equal([aV, bV, cV, dV], param_poly3.coeffs_v)
        np.testing.assert_equal([bU, 2*cU, 3*dU], param_poly3.d_coeffs_u)
        np.testing.assert_equal([bV, 2*cV, 3*dV], param_poly3.d_coeffs_v)
        np.testing.assert_equal([2*cU, 6*dU], param_poly3.d2_coeffs_u)
        np.testing.assert_equal([2*cV, 6*dV], param_poly3.d2_coeffs_v)
        self.assertEqual(pRange, param_poly3._pRange)

        pRange = None

        param_poly3 = ParamPoly3(start_position=start_position, heading=heading, length=length, aU=aU, bU=bU, cU=cU,
                                dU=dU, aV=aV, bV=bV, cV=cV, dV=dV, pRange=pRange)

        self.assertEqual(1, param_poly3._pRange)

    def test_calc_position_line(self):
        start_position = np.array([2, 5])
        length = 4
        heading = 1.2

        line = Line(start_position=start_position, heading=heading, length=length)
        result = line.calc_position(s_pos=2)

        np.testing.assert_almost_equal(np.array([2.724715509, 6.864078172]), result[0])
        self.assertEqual(heading, result[1])
        self.assertEqual(0, result[2])

    def test_calc_position_arc(self):
        # value set from test_eulerspiral.py for arcs
        start_position = np.array([1, 1])
        length = 4
        heading = 3
        curvature = 1

        arc = Arc(start_position=start_position, heading=heading, length=length, curvature=curvature)
        result = arc.calc_position(s_pos=2)
        expected_pos = np.array([-0.100044283, -0.273654682])

        np.testing.assert_almost_equal(expected_pos, result[0])
        self.assertEqual(5, result[1])
        self.assertEqual(1, result[2])

    # test_calc_position_spiral is left out, since it just calls a method from eulerspiral.py which already has a test
    def test_calc_position_poly3(self):
        start_position = np.array([2, 5])
        length = 4
        heading = 1.2
        a = 2
        b = 3
        c = 1
        d = 5

        poly3 = Poly3(start_position=start_position, heading=heading, length=length, a=a, b=b, c=c, d=d)
        result = poly3.calc_position(s_pos=2)
        expected_pos = np.array([-45.74131696, 25.7066814])

        # x and y position
        np.testing.assert_almost_equal(expected_pos, result[0])
        # orientation
        self.assertEqual(68.2, result[1])
        # curvature
        self.assertEqual((62, 5), result[2])

        # test for compute_curvature=False
        self.assertEqual(None, poly3.calc_position(s_pos=2, compute_curvature=False)[2])

    def test_calc_position_paramPoly3(self):
        start_position = np.array([2, 5])
        length = 4
        heading = 1.2
        aU = 0
        bU = 0.3
        cU = 0.1
        dU = 0.5
        aV = 0
        bV = 0
        cV = 0.2
        dV = 0.1
        pRange = 4

        param_poly3 = ParamPoly3(start_position=start_position, heading=heading, length=length, aU=aU, bU=bU, cU=cU,
                                dU=dU, aV=aV, bV=bV, cV=cV, dV=dV, pRange=pRange)
        result = param_poly3.calc_position(2.5)
        self.assertAlmostEqual(2.70780194, result[0][0])
        self.assertAlmostEqual(14.58224029, result[0][1])
        self.assertAlmostEqual(1.47537664, result[1])
        self.assertEqual((7.7, 0.5), result[2])
        result2 = param_poly3.calc_position(2.5, compute_curvature=False)
        self.assertEqual(None, result2[2])

    def test_max_abs_curvature_paramPoly3(self):
        start_position = np.array([2, 5])
        length = 4
        heading = 1.2
        aU = 0
        bU = 0.3
        cU = 0.1
        dU = 0.5
        aV = 0
        bV = 0
        cV = 0.2
        dV = 0.1
        pRange = 4

        param_poly3 = ParamPoly3(start_position=start_position, heading=heading, length=length, aU=aU, bU=bU, cU=cU,
                                 dU=dU, aV=aV, bV=bV, cV=cV, dV=dV, pRange=pRange)
        result = param_poly3.max_abs_curvature(pos=2)
        self.assertEqual((6.2, 0.5), result)
        param_poly3 = ParamPoly3(start_position=start_position, heading=heading, length=length, aU=aU, bU=bU, cU=cU,
                                 dU=-dU, aV=aV, bV=bV, cV=cV, dV=-0.9, pRange=pRange)
        result2 = param_poly3.max_abs_curvature(pos=2)
        self.assertEqual((-10.4, -0.9), result2)
        param_poly3 = ParamPoly3(start_position=start_position, heading=heading, length=length, aU=aU, bU=bU, cU=cU,
                                 dU=-0.7, aV=aV, bV=bV, cV=cV, dV=0.3, pRange=pRange)
        result3 = param_poly3.max_abs_curvature(pos=2)
        self.assertEqual((-8.2, -0.7), result3)
        param_poly3 = ParamPoly3(start_position=start_position, heading=heading, length=length, aU=aU, bU=bU, cU=cU,
                                 dU=dU, aV=aV, bV=bV, cV=cV, dV=0.6, pRange=pRange)
        result4 = param_poly3.max_abs_curvature(pos=2)
        self.assertEqual((7.6, 0.6), result4)

    def test_calc_delta_s(self):
        error_tolerance_s = 0.2

        result = calc_delta_s(curvature=3, error_tolerance=error_tolerance_s)
        self.assertAlmostEqual(0.7302967433, result)
        result2 = calc_delta_s(curvature=0, error_tolerance=error_tolerance_s)
        self.assertEqual(np.inf, result2)
        with self.assertRaises(RuntimeError):
            calc_delta_s(curvature=None, error_tolerance=error_tolerance_s)
        result3 = calc_delta_s(curvature=(3, 0.4), error_tolerance=error_tolerance_s)
        self.assertAlmostEqual(0.7302967433, result3)
        result4 = calc_delta_s(curvature=(3, -0.4), error_tolerance=error_tolerance_s)
        self.assertAlmostEqual(0.7302967433, result4)
        result5 = calc_delta_s(curvature=(3, -3), error_tolerance=error_tolerance_s)
        self.assertAlmostEqual(0.7302967433, result5)
        result6 = calc_delta_s(curvature=(3, 3), error_tolerance=error_tolerance_s)
        self.assertAlmostEqual(0.5808387447, result6)

    def test_calc_next_s(self):
        s_current = 2
        curvature = 3
        error_tolerance_s = 0.2
        min_delta_s = 0.8
        s_max = 4

        result = calc_next_s(s_current=s_current, curvature=curvature, error_tolerance=error_tolerance_s,
                             min_delta_s=min_delta_s, s_max=s_max)
        self.assertEqual(2.8, result)
        result2 = calc_next_s(s_current=s_current, curvature=curvature, error_tolerance=error_tolerance_s,
                              min_delta_s=0.6, s_max=s_max)
        self.assertAlmostEqual(2.7302967433, result2)
        result3 = calc_next_s(s_current=s_current, curvature=curvature, error_tolerance=error_tolerance_s,
                              min_delta_s=0.6, s_max=2.7402967433)
        self.assertAlmostEqual(2.7402967433, result3)
        result4 = calc_next_s(s_current=s_current, curvature=curvature, error_tolerance=error_tolerance_s,
                              min_delta_s=0.6, s_max=2)
        self.assertAlmostEqual(2, result4)


if __name__ == '__main__':
    unittest.main()
