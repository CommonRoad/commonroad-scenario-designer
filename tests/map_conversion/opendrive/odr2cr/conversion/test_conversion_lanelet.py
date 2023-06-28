import unittest
import numpy as np
from crdesigner.map_conversion.common.conversion_lanelet import ConversionLanelet, LaneletType
from crdesigner.map_conversion.opendrive.opendrive_conversion.plane_elements.plane_group import ParametricLane, \
    ParametricLaneGroup
from crdesigner.map_conversion.opendrive.opendrive_conversion.plane_elements.plane import ParametricLaneBorderGroup, \
    Border
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadPlanView import PlanView


def init_conversion_lanelet() -> ConversionLanelet:
    # create basic planview
    view = PlanView(error_tolerance_s=0.2, min_delta_s=0.3)
    view.add_line([0, 0], 0.759, 120)
    # create a basic lanelet and group
    plane_group = ParametricLaneGroup(None, None, None, True, None)
    plane_group._add_geo_length(120, False)
    # create the border group for the lane
    inner_border = Border(0.0)
    inner_border.width_coefficients.append([3.75, 0.0, 0.0, 0.0])
    inner_border.width_coefficients.append([3.75, 0.0, -0.015, 0.0004])
    inner_border.width_coefficients.append([0.0, 0.0, 0.0, 0.0])
    inner_border.width_coefficient_offsets.append(0.0)
    inner_border.width_coefficient_offsets.append(25.0)
    inner_border.width_coefficient_offsets.append(52.0)
    inner_border.reference = view

    outer_border = Border(0.0)
    outer_border.width_coefficients.append([3.75, 0.0, 0.0, 0.0])
    outer_border.width_coefficient_offsets.append(0.0)
    outer_border.reference = view

    border_group = ParametricLaneBorderGroup(inner_border, 0.0, outer_border, 0.0)

    # create the parametric lane
    lane = ParametricLane("88.0.3.0", "driving", border_group, 120, None, "left")
    # append the lane to the lane group
    plane_group.parametric_lanes.append(lane)
    # create the conversion lanelet
    lanelet = ConversionLanelet(plane_group, np.array([[0, 1], [1, 2]]), np.array([[0, 0], [1, 1]]),
                                np.array([[0, -1], [1, 0]]), 1)
    return lanelet


class TestConversionLanelet(unittest.TestCase):
    def test_equals(self):
        lanelet1 = ConversionLanelet(None, np.array([[0.5, 0.5], [1, 0]]), np.array([[0.0, 0.0], [0.5, 0.5]]),
                                     np.array([[-0.5, -0.5], [1, 0]]), 1)
        lanelet1.lanelet_id = "115.2.3.-1"
        lanelet2 = ConversionLanelet(None, np.array([[0.5, 0.5], [1, 0]]), np.array([[0.0, 0.0], [0.5, 0.5]]),
                                     np.array([[-0.5, -0.5], [1, 0]]), 1)
        lanelet2.lanelet_id = "115.2.3.-1"
        self.assertTrue(lanelet1.__eq__(lanelet2))
        lanelet1.lanelet_id = "foo"
        self.assertFalse(lanelet1.__eq__(lanelet2))

    def test_lanelet_type(self):
        lanelet1 = ConversionLanelet(None, np.array([[0.5, 0.5], [1, 0]]), np.array([[0.0, 0.0], [0.5, 0.5]]),
                                     np.array([[-0.5, -0.5], [1, 0]]), 1)
        lanelet1.lanelet_type = "driving"
        true_type = {LaneletType.URBAN}
        self.assertEqual(true_type, lanelet1.lanelet_type)

        lanelet1.lanelet_type = "exit"
        true_type = {LaneletType.EXIT_RAMP, LaneletType.URBAN}
        self.assertEqual(true_type, lanelet1.lanelet_type)

        lanelet1.lanelet_type = "foo"
        true_type = {LaneletType.URBAN}
        self.assertEqual(true_type, lanelet1.lanelet_type)

        lanelet2 = \
            ConversionLanelet(None, np.array([[0.5, 0.5], [1, 0]]), np.array([[0.0, 0.0], [0.5, 0.5]]),
                              np.array([[-0.5, -0.5], [1, 0]]), 1)
        lanelet2.lanelet_type = "driving"
        true_type = {LaneletType.URBAN}
        self.assertEqual(true_type, lanelet2.lanelet_type)

        lanelet2.lanelet_type = "exit"
        true_type = {LaneletType.EXIT_RAMP, LaneletType.URBAN}
        self.assertEqual(true_type, lanelet2.lanelet_type)

        lanelet2.lanelet_type = "foo"
        true_type = {LaneletType.URBAN}
        self.assertEqual(true_type, lanelet2.lanelet_type)

    def test_lanelet_id(self):
        lanelet1 = ConversionLanelet(None, np.array([[0.5, 0.5], [1, 0]]), np.array([[0.0, 0.0], [0.5, 0.5]]),
                                     np.array([[-0.5, -0.5], [1, 0]]), 1)
        true_id = 1
        lanelet1.lanelet_id = 1
        self.assertEqual(true_id, lanelet1.lanelet_id)

        true_id = "114.0.4.-1"
        lanelet1.lanelet_id = true_id
        self.assertEqual(true_id, lanelet1.lanelet_id)

    def test_left_vertices(self):
        lanelet1 = ConversionLanelet(None, np.array([[0.5, 0.5], [1, 0]]), np.array([[0.0, 0.0], [0.5, 0.5]]),
                                     np.array([[-0.5, -0.5], [1, 0]]), 1)

        np.testing.assert_equal([[0.5, 0.5], [1, 0]], lanelet1.left_vertices.tolist())

        lanelet1.left_vertices = []
        self.assertListEqual([], lanelet1.left_vertices)

        lanelet1.left_vertices = [[13.95, 59.12], [22.56, 66.20]]
        self.assertListEqual([[13.95, 59.12], [22.56, 66.20]], lanelet1.left_vertices)

    def test_right_vertices(self):
        lanelet1 = ConversionLanelet(None, np.array([[0.5, 0.5], [1, 0]]), np.array([[0.0, 0.0], [0.5, 0.5]]),
                                     np.array([[-0.5, -0.5], [1, 0]]), 1)

        np.testing.assert_equal([[-0.5, -0.5], [1, 0]], lanelet1.right_vertices.tolist())

        lanelet1.right_vertices = []
        self.assertListEqual([], lanelet1.right_vertices)

        lanelet1.right_vertices = [[13.95, 59.12], [22.56, 66.20]]
        self.assertListEqual([[13.95, 59.12], [22.56, 66.20]], lanelet1.right_vertices)

    def test_center_vertices(self):
        lanelet1 = ConversionLanelet(None, np.array([[0.5, 0.5], [1, 0]]), np.array([[0.0, 0.0], [0.5, 0.5]]),
                                     np.array([[0.0, 0.0], [0.5, 0.5]]), 1)

        np.testing.assert_equal([[0.0, 0.0], [0.5, 0.5]], lanelet1.center_vertices.tolist())

        lanelet1.center_vertices = []
        self.assertListEqual([], lanelet1.center_vertices)

        lanelet1.center_vertices = [[13.95, 59.12], [22.56, 66.20]]
        self.assertListEqual([[13.95, 59.12], [22.56, 66.20]], lanelet1.center_vertices)

    def test_predecessor(self):
        lanelet = ConversionLanelet(None, np.array([[0.5, 0.5], [1, 0]]), np.array([[0.0, 0.0], [0.5, 0.5]]),
                                    np.array([[0.0, 0.0], [0.5, 0.5]]), 1)

        self.assertEqual([], lanelet.predecessor)

        lanelet.predecessor = ["6481.7.3.-1"]
        self.assertListEqual(["6481.7.3.-1"], lanelet.predecessor)

        lanelet.predecessor = [69, 70]
        self.assertListEqual([69, 70], lanelet.predecessor)

    def test_successor(self):
        lanelet = ConversionLanelet(None, np.array([[0.5, 0.5], [1, 0]]), np.array([[0.0, 0.0], [0.5, 0.5]]),
                                    np.array([[0.0, 0.0], [0.5, 0.5]]), 1)

        self.assertEqual([], lanelet.successor)

        lanelet.successor = ["210.0.-3.-1"]
        self.assertListEqual(["210.0.-3.-1"], lanelet.successor)

        lanelet.successor = [60, 61]
        self.assertListEqual([60, 61], lanelet.successor)

    def test_adj_left(self):
        lanelet = ConversionLanelet(None, np.array([[0.5, 0.5], [1, 0]]), np.array([[0.0, 0.0], [0.5, 0.5]]),
                                    np.array([[0.0, 0.0], [0.5, 0.5]]), 1)

        lanelet.adj_left = "3212.0.-1.-1"
        self.assertEqual("3212.0.-1.-1", lanelet.adj_left)

        lanelet.adj_left = 72
        self.assertEqual(72, lanelet.adj_left)

    def test_adj_left_same_direction(self):
        lanelet = ConversionLanelet(None, np.array([[0.5, 0.5], [1, 0]]), np.array([[0.0, 0.0], [0.5, 0.5]]),
                                    np.array([[0.0, 0.0], [0.5, 0.5]]), 1)
        lanelet.adj_left_same_direction = True
        self.assertEqual(True, lanelet.adj_left_same_direction)

        lanelet.adj_left_same_direction = False
        self.assertEqual(False, lanelet.adj_left_same_direction)

    def test_adj_right(self):
        lanelet = ConversionLanelet(None, np.array([[0.5, 0.5], [1, 0]]), np.array([[0.0, 0.0], [0.5, 0.5]]),
                                    np.array([[0.0, 0.0], [0.5, 0.5]]), 1)

        lanelet.adj_right = "3212.0.-1.-1"
        self.assertEqual("3212.0.-1.-1", lanelet.adj_right)

        lanelet.adj_right = 72
        self.assertEqual(72, lanelet.adj_right)

    def test_adj_right_same_direction(self):
        lanelet = ConversionLanelet(None, np.array([[0.5, 0.5], [1, 0]]), np.array([[0.0, 0.0], [0.5, 0.5]]),
                                    np.array([[0.0, 0.0], [0.5, 0.5]]), 1)
        lanelet.adj_right_same_direction = True
        self.assertEqual(True, lanelet.adj_right_same_direction)

        lanelet.adj_right_same_direction = False
        self.assertEqual(False, lanelet.adj_right_same_direction)

    def test_concatenate(self):
        lanelet = ConversionLanelet(None, np.array([[0, 1], [1, 2]]), np.array([[0, 0], [1, 1]]),
                                    np.array([[0, -1], [1, 0]]), 1)
        lanelet_conc = ConversionLanelet(None, np.array([[1, 2], [2, 2]]), np.array([[1, 1], [2, 1]]),
                                         np.array([[1, 0], [2, 0]]), 1)
        lanelet.concatenate(lanelet_conc, False)
        # test 1: Initial lanelet has same end vertices as start vertices of the concatenate vertex
        true_left_vertices = [[0, 1], [1, 2], [2, 2]]
        true_center_vertices = [[0, 0], [1, 1], [2, 1]]
        true_right_vertices = [[0, -1], [1, 0], [2, 0]]

        self.assertListEqual(true_left_vertices, lanelet.left_vertices.tolist())
        self.assertListEqual(true_center_vertices, lanelet.center_vertices.tolist())
        self.assertListEqual(true_right_vertices, lanelet.right_vertices.tolist())
        # test 2: Initial lanelet has different end vertices as start vertices of the concatenate vertex

        lanelet = ConversionLanelet(None, np.array([[0, 1], [1, 2]]), np.array([[0, 0], [1, 1]]),
                                    np.array([[0, -1], [1, 0]]), 1)

        lanelet_conc = ConversionLanelet(None, np.array([[2, 2], [3, 2]]), np.array([[2, 1], [3, 1]]),
                                         np.array([[2, 0], [3, 0]]), 1)

        lanelet.concatenate(lanelet_conc, False)

        true_left_vertices = [[0, 1], [1, 2], [2, 2], [3, 2]]
        true_center_vertices = [[0, 0], [1, 1], [2, 1], [3, 1]]
        true_right_vertices = [[0, -1], [1, 0], [2, 0], [3, 0]]

        self.assertListEqual(true_left_vertices, lanelet.left_vertices.tolist())
        self.assertListEqual(true_center_vertices, lanelet.center_vertices.tolist())
        self.assertListEqual(true_right_vertices, lanelet.right_vertices.tolist())

    def test_calc_border(self):
        lanelet = init_conversion_lanelet()
        # basic test
        coords, hdg, curv, len = lanelet.calc_border("inner", 0, 0.0, True)
        np.testing.assert_almost_equal(coords.tolist(), [-2.58073599, 2.72071714], 7)
        # test with additional offset
        coords, hdg, curv, len = lanelet.calc_border("inner", 0, 5.0, True)
        np.testing.assert_almost_equal(coords.tolist(), [-6.02171732, 6.34833998], 7)

    def test_calc_width_at_end(self):
        lanelet = init_conversion_lanelet()
        width_at_end = lanelet.calc_width_at_end()
        np.testing.assert_almost_equal(width_at_end, 3.7500000, 7)

    def test_calc_width_at_start(self):
        lanelet = init_conversion_lanelet()
        width_at_start = lanelet.calc_width_at_start()
        np.testing.assert_almost_equal(width_at_start, 0.0, 7)

    def test_calc_width(self):
        lanelet = init_conversion_lanelet()
        # test at s = 0
        norm = lanelet.calc_width(0)
        true_inner_pos = np.array([-2.58073599, 2.72071714])
        true_outer_pos = np.array([-2.58073599, 2.72071714])
        true_norm = np.linalg.norm(true_inner_pos - true_outer_pos)
        self.assertEqual(true_norm, norm)
        # test at s = 37.5
        norm = lanelet.calc_width(37.5)
        true_inner_pos = np.array([25.70174203, 27.39444492])
        true_outer_pos = np.array([24.62643537, 28.52807706])
        true_norm = np.linalg.norm(true_inner_pos - true_outer_pos)
        self.assertAlmostEqual(true_norm, norm, 3)

    def test_length(self):
        lanelet = init_conversion_lanelet()
        len = lanelet.length
        self.assertEqual(120, len)

    def test_has_zero_width_everywhere(self):
        lanelet = init_conversion_lanelet()
        self.assertFalse(lanelet.has_zero_width_everywhere())

        lanelet.parametric_lane_group.parametric_lanes[0].border_group.outer_border.width_coefficients.clear()
        lanelet.parametric_lane_group.parametric_lanes[0].border_group.outer_border.width_coefficients\
            .append([0.0, 0.0, 0.0, 0.0])
        self.assertTrue(lanelet.has_zero_width_everywhere())

    def test_first_zero_width_change_position(self):
        lanelet = init_conversion_lanelet()
        res = lanelet.first_zero_width_change_position(False, 0.0)
        np.testing.assert_almost_equal((120, 3.75000), res, 5)
        # change outer border width coefficients to a polynomial with roots
        lanelet.parametric_lane_group.parametric_lanes[0].border_group.outer_border.width_coefficients.clear()
        lanelet.parametric_lane_group.parametric_lanes[0].border_group.outer_border.width_coefficients\
            .append([3.75, 0.0, -0.015, 0.0004])
        # roots of above polynomial are 0, 25
        res = lanelet.first_zero_width_change_position(False, 0.0)
        np.testing.assert_almost_equal((25., 3.125), res, 3)

    def test_maximum_width(self):
        lanelet = init_conversion_lanelet()
        max_width = lanelet.maximum_width()
        self.assertEqual(3.75, max_width)
        # change outer border width coefficients to a polynomial with roots
        lanelet.parametric_lane_group.parametric_lanes[0].border_group.outer_border.width_coefficients.clear()
        lanelet.parametric_lane_group.parametric_lanes[0].border_group.outer_border.width_coefficients\
            .append([3.75, 0.0, -0.015, 0.0004])
        self.assertEqual(3.75, max_width)

    def test_optimal_join_split_values(self):
        lanelet = init_conversion_lanelet()
        merge_pos, merge_width = lanelet.optimal_join_split_values(True, False, 3.75)
        # with border coefficients of [0.0, ...], no roots exist -> merge pos is at end of lanelet
        true_merge_pos = 120
        true_merge_width = 3.75
        self.assertAlmostEqual(true_merge_pos, merge_pos, 7)
        self.assertAlmostEqual(true_merge_width, merge_width, 7)

        # now polynomial has real roots, merge pos is at roots
        lanelet.parametric_lane_group.parametric_lanes[0].border_group.outer_border.width_coefficients.clear()
        lanelet.parametric_lane_group.parametric_lanes[0].border_group.outer_border.width_coefficients\
            .append([3.75, 0.0, -0.015, 0.0004])
        merge_pos, merge_width = lanelet.optimal_join_split_values(True, False, 0.0)
        true_merge_pos = 25.0
        true_merge_width = 3.125
        self.assertAlmostEqual(true_merge_pos, merge_pos, 7)
        self.assertAlmostEqual(true_merge_width, merge_width, 7)

        # test with both a split at start and merge at end, need to adjust length of lane for that
        lanelet.parametric_lane_group.parametric_lanes[0].length = 40
        merge_pos, merge_width = lanelet.optimal_join_split_values(True, True, 0.0)
        # merge_pos should be at 0.45 * length
        true_merge_pos = 0.45 * 40
        true_merge_width = lanelet.calc_width(merge_pos)

        self.assertAlmostEqual(true_merge_pos, merge_pos, 7)
        self.assertAlmostEqual(true_merge_width, merge_width, 7)

        lanelet.parametric_lane_group.parametric_lanes[0].length = 80
        merge_pos, merge_width = lanelet.optimal_join_split_values(False, True, 0.0)
        # merge_pos should be at 0.45 * length
        true_merge_pos = 0.55 * 80
        true_merge_width = lanelet.calc_width(merge_pos)

        self.assertAlmostEqual(true_merge_pos, merge_pos, 7)
        self.assertAlmostEqual(true_merge_width, merge_width, 7)
