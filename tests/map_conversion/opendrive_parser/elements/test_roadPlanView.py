import unittest
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadPlanView import *


class TestRoadPlanView(unittest.TestCase):
    def test_initialize_plan_view(self):
        plan_view = PlanView()
        self.assertEqual(0.2, plan_view._error_tolerance_s)
        self.assertEqual(0.3, plan_view._min_delta_s)

    def test_add_geo_length(self):
        plan_view = PlanView()
        length = 3.2
        plan_view._add_geo_length(length)
        self.assertEqual(plan_view.length, plan_view._geo_lengths[-1])

    def test_add_geometries(self):
        plan_view = PlanView()
        # line
        start_pos = np.array([0, 0])
        heading = 1
        length = 2.3
        plan_view.add_line(start_pos=start_pos, heading=heading, length=length)
        # spiral
        start_pos = np.array([2.3, 4])
        heading = 0.4
        length = 2
        curvStart = 1
        curvEnd = 1.2
        plan_view.add_spiral(start_pos=start_pos, heading=heading, length=length, curv_start=curvStart, curv_end=curvEnd)
        # arc
        start_pos = np.array([4, 5])
        heading = 1.2
        length = 2.3
        curvature = 1
        plan_view.add_arc(start_pos=start_pos, heading=heading, length=length, curvature=curvature)
        # param poly 3
        start_pos = np.array([8, 9])
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
        plan_view.add_param_poly3(start_pos=start_pos, heading=heading, length=length, aU=aU, bU=bU, cU=cU, dU=dU,
                                  aV=aV, bV=bV, cV=cV, dV=dV, pRange=pRange)
        # poly 3
        start_pos = np.array([2, 5])
        length = 4
        heading = 1.2
        a = 2
        b = 3
        c = 1
        d = 5
        plan_view.add_poly3(start_pos=start_pos, heading=heading, length=length, a=a, b=b, c=c, d=d)

        self.assertIsInstance(plan_view._geometries[0], Line)
        self.assertIsInstance(plan_view._geometries[1], Spiral)
        self.assertIsInstance(plan_view._geometries[2], Arc)
        self.assertIsInstance(plan_view._geometries[3], ParamPoly3)
        self.assertIsInstance(plan_view._geometries[4], Poly3)
        self.assertEqual(14.6, plan_view.length)

        # calc_geometry
        s_pos = 12.6
        result = plan_view.calc_geometry(s_pos=s_pos)

        # values from test_geometry for poly 3
        expected_pos = np.array([-45.74131696, 25.7066814])
        # x and y position
        np.testing.assert_almost_equal(expected_pos, result[0])
        # orientation
        self.assertEqual(68.2, result[1])
        # curvature
        self.assertEqual((62, 5), result[2])
        # max_geometry
        self.assertEqual(14.6, result[3])

        result = plan_view.calc_geometry(s_pos=s_pos, reverse=True)
        self.assertEqual(4, result[3])

    def test_precalculate(self):
        plan_view = PlanView()
        # line
        start_pos = np.array([0, 0])
        heading = 1
        length = 2.3
        plan_view.add_line(start_pos=start_pos, heading=heading, length=length)
        # spiral
        start_pos = np.array([2.3, 4])
        heading = 0.4
        length = 2
        curvStart = 1
        curvEnd = 1.2
        plan_view.add_spiral(start_pos=start_pos, heading=heading, length=length, curv_start=curvStart, curv_end=curvEnd)
        # arc
        start_pos = np.array([4, 5])
        heading = 1.2
        length = 2.3
        curvature = 1
        plan_view.add_arc(start_pos=start_pos, heading=heading, length=length, curvature=curvature)
        # param poly 3
        start_pos = np.array([8, 9])
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
        plan_view.add_param_poly3(start_pos=start_pos, heading=heading, length=length, aU=aU, bU=bU, cU=cU, dU=dU,
                                  aV=aV, bV=bV, cV=cV, dV=dV, pRange=pRange)
        # poly 3
        start_pos = np.array([2, 5])
        length = 4
        heading = 1.2
        a = 2
        b = 3
        c = 1
        d = 5
        plan_view.add_poly3(start_pos=start_pos, heading=heading, length=length, a=a, b=b, c=c, d=d)

        plan_view.precalculate()
        expected_res = [0, 0, 0, 1]
        np.testing.assert_equal(expected_res, plan_view._precalculation[0])
        expected_res1 = [2.3, 2.3, 4, 0.4]
        np.testing.assert_equal(expected_res1, plan_view._precalculation[1])


if __name__ == '__main__':
    unittest.main()
