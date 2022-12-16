import unittest
from crdesigner.map_conversion.opendrive.opendrive_conversion.plane_elements.plane import *
from crdesigner.map_conversion.opendrive.opendrive_parser.elements import roadLanes
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadPlanView import PlanView


class TestParametricLaneBorderGroup(unittest.TestCase):
    def test_initialize_parametric_lane_border_group(self):
        inner_border = Border(0.0)
        inner_border.width_coefficients.append([-5.0, 0.0, 0.0, 0.0])
        inner_border.width_coefficient_offsets.append(0.0)
        inner_border_offset = 10.0

        outer_border = Border(10.0)
        outer_border.width_coefficients.append([-3.25, -0.5, -0.01, -0.002])
        outer_border.width_coefficient_offsets.append(0.0)
        outer_border_offset = 15.0

        group = ParametricLaneBorderGroup(inner_border, inner_border_offset, outer_border, outer_border_offset)

        self.assertListEqual(inner_border.width_coefficients, group.inner_border.width_coefficients)
        self.assertListEqual(inner_border.width_coefficient_offsets, group.inner_border.width_coefficient_offsets)
        self.assertEqual(inner_border.ref_offset, group.inner_border.ref_offset)
        self.assertEqual(inner_border_offset, group.inner_border_offset)
        self.assertListEqual(outer_border.width_coefficients, group.outer_border.width_coefficients)
        self.assertListEqual(outer_border.width_coefficient_offsets, group.outer_border.width_coefficient_offsets)
        self.assertEqual(outer_border.ref_offset, group.outer_border.ref_offset)
        self.assertEqual(outer_border_offset, group.outer_border_offset)

    def test_calc_border_position(self):
        view = PlanView(error_tolerance_s=0.2, min_delta_s=0.3)
        view.add_poly3(0.0, 0, 100, 1, 0.2, 0.02, 0.001)

        reference_border = Border(0.0)
        reference_border.width_coefficients.append([0.0])
        reference_border.width_coefficient_offsets.append(0.0)
        reference_border.reference = view

        inner_border = Border()
        inner_border.width_coefficients.append([-1.0, 0.0, 0.0, 0.0])
        inner_border.width_coefficient_offsets.append(0.0)
        inner_border.reference = reference_border
        outer_border = Border()
        outer_border.width_coefficients.append([-3.65, 0.0, 0.0, 0.0])
        outer_border.width_coefficient_offsets.append(0.0)
        outer_border.reference = reference_border

        group = ParametricLaneBorderGroup(inner_border, 0.0, outer_border, 0.0)
        # test that selecting inner/outer border works correctly and outputs correct parameters
        coords, tan, curv, max_geo_len = group.calc_border_position("inner", 20.0, 0.0, False, False, True)
        true_inner_coords = [20.808, 21.588]
        true_inner_tan = 2.2
        true_inner_curv = (0.16, 0.001)
        true_inner_geo_len = 100
        np.testing.assert_almost_equal(coords.tolist(), true_inner_coords, 3)
        self.assertTupleEqual(true_inner_curv, curv)
        self.assertEqual(true_inner_tan, tan)
        self.assertEqual(true_inner_geo_len, max_geo_len)

        coords, tan, curv, max_geo_len = group.calc_border_position("outer", 20.0, 0.0, False, False, True)
        true_outer_coords = [22.951, 23.148]
        true_outer_tan = 2.2
        true_outer_curv = (0.16, 0.001)
        true_outer_geo_len = 100
        np.testing.assert_almost_equal(coords.tolist(), true_outer_coords, 3)
        self.assertTupleEqual(true_outer_curv, curv)
        self.assertEqual(true_outer_tan, tan)
        self.assertEqual(true_outer_geo_len, max_geo_len)
        # test that calling the function with any other string than inner/outer raises a ValueError
        self.assertRaises(ValueError, group.calc_border_position, "foo", 20.0, 0.0, False, False, True)

    def test_get_width_coefficients(self):
        inner_border = Border()
        inner_border.width_coefficients.append([-1.0, 0.0, 0.0, 0.0])
        inner_border.width_coefficient_offsets.append(0.0)
        outer_border = Border(5.0)
        outer_border.width_coefficients.append([-3.65, 0.0, 0.0, 0.0])
        outer_border.width_coefficients.append([-5.0, -1.0, -0.1, -0.02])
        outer_border.width_coefficient_offsets.append(0.0)
        outer_border.width_coefficient_offsets.append(6.0)

        group = ParametricLaneBorderGroup(inner_border, 0.0, outer_border, 10.0)
        # should return second list of coefficients
        width_coefficients = group.get_width_coefficients()
        self.assertListEqual(outer_border.width_coefficients[1], width_coefficients)

        group = ParametricLaneBorderGroup(inner_border, 0.0, outer_border, 6.0)
        # should return second list of coefficients
        width_coefficients = group.get_width_coefficients()
        self.assertListEqual(outer_border.width_coefficients[1], width_coefficients)

        group = ParametricLaneBorderGroup(inner_border, 0.0, outer_border, 3.0)
        # should return first list of coefficients
        width_coefficients = group.get_width_coefficients()
        self.assertListEqual(outer_border.width_coefficients[0], width_coefficients)

        group = ParametricLaneBorderGroup(inner_border, 0.0, outer_border, 0.0)
        # should return first list of coefficients
        width_coefficients = group.get_width_coefficients()
        self.assertListEqual(outer_border.width_coefficients[0], width_coefficients)


class TestParametricLane(unittest.TestCase):
    def test_initialize_parametric_lane(self):
        id = '1'
        type = 'test'
        group = ParametricLaneBorderGroup()
        length = 5.0
        roadMark = roadLanes.RoadMark()
        roadMark.__setattr__('SOffset', 5)
        side = "right"
        parametric_lane = ParametricLane(id, type, group, length, roadMark, side)
        self.assertEqual(group, parametric_lane.border_group)
        self.assertEqual(id, parametric_lane.id_)
        self.assertEqual(type, parametric_lane.type_)
        self.assertEqual(length, parametric_lane.length)
        self.assertEqual(False, parametric_lane.reverse)
        self.assertEqual(roadMark, parametric_lane.line_marking)
        self.assertEqual(side, parametric_lane.side)

    @staticmethod
    def init_lane() -> ParametricLane:
        view = PlanView(error_tolerance_s=0.2, min_delta_s=0.3)
        view.add_line([26.11, 26.11], 0.7853, 46.911)
        view.add_spiral([59.342, 59.342], 0.7853, 11.25, 0.0, -0.0125)
        view.add_arc([67.479, 67.106], 0.715, 177.246, -0.0125)

        inner_border = Border()
        inner_border.width_coefficients.append([0.0, 0.0, 0.0, 0.0])
        inner_border.width_coefficient_offsets.append(0.0)
        inner_border.reference = view
        outer_border = Border()
        outer_border.width_coefficients.append([-1.0, 0.0, 0.0, 0.0])
        outer_border.width_coefficient_offsets.append(0.0)
        outer_border.reference = view

        group = ParametricLaneBorderGroup(inner_border, 0.0, outer_border, 10.0)
        return ParametricLane("114.0.-1.0", "restricted", group, 6.0, None, "right")

    def test_calc_border(self):
        view = PlanView(error_tolerance_s=0.2, min_delta_s=0.3)
        view.add_line([26.11, 26.11], 0.7853, 46.911)
        view.add_spiral([59.342, 59.342], 0.7853, 11.25, 0.0, -0.0125)
        view.add_arc([67.479, 67.106], 0.715, 177.246, -0.0125)

        inner_border = Border()
        inner_border.width_coefficients.append([0.0, 0.0, 0.0, 0.0])
        inner_border.width_coefficient_offsets.append(0.0)
        inner_border.reference = view
        outer_border = Border()
        outer_border.width_coefficients.append([-1.0, 0.0, 0.0, 0.0])
        outer_border.width_coefficient_offsets.append(0.0)
        outer_border.reference = view

        group = ParametricLaneBorderGroup(inner_border, 0.0, outer_border, 10.0)
        parametric_lane = ParametricLane("114.0.-1.0", "restricted", group, 6.0, None, "right")
        # geometry is line
        coords, tan, curv, len = parametric_lane.calc_border("inner", 0, width_offset=0.0, compute_curvature=False)
        self.assertListEqual([26.11, 26.11], coords.tolist())
        # geometry is spiral
        coords, tan, curv, len = parametric_lane.calc_border("inner", 47, width_offset=0.0, compute_curvature=False)
        np.testing.assert_almost_equal(coords.tolist(), [59.404, 59.404], 3)

        # test with length == border_pos, so is_last_pos is True
        coords, tan, curv, len = parametric_lane.calc_border("inner", 6.0, width_offset=0.0, compute_curvature=False)
        np.testing.assert_almost_equal(coords.tolist(), [30.353, 30.352], 3)

    def test_calc_width(self):
        parametric_lane = self.init_lane()
        width = parametric_lane.calc_width(10)
        true_width = np.sqrt((33.181-40.960)**2+(33.180-39.543)**2)
        self.assertAlmostEqual(true_width, width, 3)

    def test_has_zero_width_everywhere(self):
        parametric_lane = self.init_lane()
        self.assertFalse(parametric_lane.has_zero_width_everywhere())
        parametric_lane.border_group.outer_border.width_coefficients.clear()
        parametric_lane.border_group.outer_border.width_coefficients.append([0.0, 0.0, 0.0, 0.0])
        self.assertTrue(parametric_lane.has_zero_width_everywhere())

    def test_calc_vertices(self):
        parametric_lane = self.init_lane()
        parametric_lane.border_group.outer_border_offset = 0.0
        parametric_lane.border_group.inner_border.width_coefficients.clear()
        parametric_lane.border_group.inner_border.width_coefficients.append([5, 0, 0, 0])
        # test on straight-line geometry of the initialised lane
        # function should create three vertices: start, middle and end
        parametric_lane.length = 46.911
        left, right = parametric_lane.calc_vertices(error_tolerance=0.2, min_delta_s=0.3)

        # test for calculating the vertices without sampling
        self.assertEqual(94, len(left))
        self.assertEqual(94, len(right))
        # test for calculating the vertices with sampling
        # self.assertEqual(3, len(left))
        # self.assertEqual(3, len(right))

        # test that inner border vertices are offset (in t-direction) by 5
        # test for calculating the vertices without sampling
        np.testing.assert_almost_equal([22.574, 29.645], left[0], 3)
        np.testing.assert_almost_equal([55.806, 62.877], left[-1], 3)
        # test for calculating the vertices with sampling
        # np.testing.assert_almost_equal([[22.574, 29.645], [39.161, 46.229], [55.806, 62.877]], left, 3)

        # test that outer border vertices are offset (in t-direction) by -1
        # test for calculating the vertices without sampling
        np.testing.assert_almost_equal([26.817, 25.402], right[0], 3)
        np.testing.assert_almost_equal([60.049, 58.634], right[-1], 3)
        # test for calculating the vertices with sampling
        # np.testing.assert_almost_equal([[26.817, 25.402], [43.404, 41.986], [60.049, 58.634]], right, 3)

        # test that parametric lane with length < 0 returns empty lists
        parametric_lane.length = -1
        left, right = parametric_lane.calc_vertices(error_tolerance=0.2, min_delta_s=0.3)
        self.assertListEqual([], left.tolist())
        self.assertListEqual([], right.tolist())

    def test_zero_width_change_positions(self):
        lane = self.init_lane()
        lane.length = 30
        lane.border_group.outer_border.width_coefficients.clear()
        lane.border_group.outer_border.width_coefficient_offsets.clear()
        lane.border_group.outer_border.width_coefficients.append([0, 0, 0, 0])
        lane.border_group.outer_border.width_coefficient_offsets.append(0)
        roots = lane.zero_width_change_positions()
        # test with no roots
        self.assertEqual([], roots.tolist())
        # test with real root
        lane.border_group.outer_border.width_coefficients.clear()
        lane.border_group.outer_border.width_coefficient_offsets.clear()
        lane.border_group.outer_border.width_coefficients.append([3.65, 0.0, -0.012166666666666666,
                                                                  0.00027037037037037036])
        lane.border_group.outer_border.width_coefficients.append([0, 0, 0, 0])
        lane.border_group.outer_border.width_coefficient_offsets.append(0)
        lane.border_group.outer_border.width_coefficient_offsets.append(30)
        roots = lane.zero_width_change_positions()
        true_roots = P.polyroots(P.polyder(lane.border_group.outer_border.width_coefficients[0]))
        np.testing.assert_almost_equal(true_roots, roots, 3)
        # test that reverse works
        lane.reverse = True
        roots = lane.zero_width_change_positions()
        true_roots = true_roots[::-1]
        np.testing.assert_almost_equal(true_roots, roots, 3)

    def test_get_maximum_width(self):
        lane = self.init_lane()
        # test with non-reversed lane
        max_pos_and_val = lane.maximum_width(False)
        self.assertTupleEqual((0.0, 1.0), max_pos_and_val)
        # test with reversed lane
        max_pos_and_val = lane.maximum_width(True)
        self.assertTupleEqual((6.0, 1.0), max_pos_and_val)


if __name__ == '__main__':
    unittest.main()
