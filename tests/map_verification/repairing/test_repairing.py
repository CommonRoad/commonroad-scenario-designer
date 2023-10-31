import unittest

import numpy as np
from commonroad.scenario.intersection import Intersection
from commonroad.scenario.lanelet import Lanelet, LaneletNetwork, StopLine, LineMarking
from commonroad.scenario.scenario import ScenarioID
from commonroad.scenario.traffic_sign import TrafficSign, TrafficSignElement, TrafficSignIDGermany, \
    TrafficSignIDZamunda
from commonroad.scenario.traffic_light import TrafficLight, TrafficLightCycleElement, TrafficLightState, \
    TrafficLightCycle

from crdesigner.verification_repairing.repairing.traffic_light_repairing import TrafficLightRepairing
from crdesigner.verification_repairing.repairing.traffic_sign_repairing import TrafficSignRepairing
from crdesigner.verification_repairing.repairing.lanelet_repairing import LaneletRepairing
from crdesigner.verification_repairing.repairing.general_repairing import GeneralRepairing


class TestGeneralRepairing(unittest.TestCase):
    """
    The class tests the repairing of general elements.
    """
    def setUp(self) -> None:
        left_polyline_1 = np.array([[0., 1.], [1., 1.], [2., 1.]])
        center_polyline_1 = np.array([[0., .5], [1., .5], [2., .5]])
        right_polyline_1 = np.array([[0., 0.], [1., 0.], [2., 0.]])
        left_polyline_2 = np.array([[0., 0.], [1., 0.], [2., 0.]])
        center_polyline_2 = np.array([[0., -.5], [1., -.5], [2., -.5]])
        right_polyline_2 = np.array([[0., -1.], [1., -1.], [2., -1.]])

        # self.stop_line = StopLine(np.array([0., 0.]), np.array([1., 1.]), LineMarking.NO_MARKING, {9}, set(),
        # stop_line_id=1)
        self.stop_line = StopLine(np.array([0., 0.]), np.array([1., 1.]), LineMarking.NO_MARKING, {9}, set())

        self.lanelet_1 = Lanelet(left_polyline_1, center_polyline_1, right_polyline_1, 1, stop_line=self.stop_line)
        self.lanelet_2 = Lanelet(left_polyline_2, center_polyline_2, right_polyline_2, 2)

        self.traffic_light = TrafficLight(1, np.array([0.0, 0.0]))

        # incoming_element_0 = IncomingGroup(1, incoming_lanelets={1})
        # incoming_element_1 = IncomingGroup(1, incoming_lanelets={2})
        # self.intersection = Intersection(1, incomings=[incoming_element_0, incoming_element_1])
        self.intersection = Intersection(1, incomings=[])

        traffic_sign_element = TrafficSignElement(TrafficSignIDGermany.TOWN_SIGN, ['Munich'])
        self.traffic_sign = TrafficSign(1, [traffic_sign_element], {1}, np.array([0., 0.]))

        self.network = LaneletNetwork()
        self.network.add_lanelet(self.lanelet_1)
        self.network.add_lanelet(self.lanelet_2)
        self.network.add_intersection(self.intersection)
        self.network.add_traffic_light(self.traffic_light, {1})
        self.network.add_traffic_sign(self.traffic_sign, {1})
        self.repairer = GeneralRepairing(self.network)

    def test_unique_id(self):
        self.repairer.repair_unique_id((self.lanelet_1.lanelet_id,))
        self.assertNotEqual(self.lanelet_1.lanelet_id, 1)
        self.assertEqual(self.lanelet_1.lanelet_id, 3)

        self.repairer.repair_unique_id((self.lanelet_2.lanelet_id,))
        self.assertEqual(self.lanelet_2.lanelet_id, 4)

        self.repairer.repair_unique_id((self.traffic_light.traffic_light_id,))
        self.assertNotEqual(self.traffic_light.traffic_light_id, 1)

        self.repairer.repair_unique_id((self.traffic_sign.traffic_sign_id,))
        self.assertNotEqual(self.traffic_sign.traffic_sign_id, 1)

        self.repairer.repair_unique_id((self.intersection.intersection_id,))
        self.assertNotEqual(self.intersection.intersection_id, 1)


class TestLaneletRepairing(unittest.TestCase):
    """
    The class tests the repairing of lanelet elements.
    """

    def setUp(self) -> None:
        left_polyline_1 = np.array([[0., 1.], [1., 1.], [2., 1.]])
        center_polyline_1 = np.array([[0., .5], [1., .5], [2., .5]])
        right_polyline_1 = np.array([[0., 0.], [1., 0.], [2., 0.]])
        left_polyline_2 = np.array([[0., 0.], [1., 0.], [2., 0.]])
        center_polyline_2 = np.array([[0., -.5], [1., -.5], [2., -.5]])
        right_polyline_2 = np.array([[0., -1.], [1., -1.], [2., -1.]])

        self.lanelet_1 = Lanelet(left_polyline_1, center_polyline_1, right_polyline_1, 1)
        self.lanelet_2 = Lanelet(left_polyline_2, center_polyline_2, right_polyline_2, 2)

        self.network = LaneletNetwork()
        self.network.add_lanelet(self.lanelet_1)
        self.network.add_lanelet(self.lanelet_2)
        self.scenario_id = ScenarioID()
        self.lanelet_repairer = LaneletRepairing(self.network)

    def test_same_vertices_size(self):
        self.lanelet_1.left_vertices = np.array([[0., 1.], [2., 1.]])

        self.lanelet_repairer.repair_same_vertices_size((1,))

        self.assertEqual(3, len(self.lanelet_1.left_vertices))
        self.assertEqual([[0., 1.], [1., 1.], [2., 1.]], self.lanelet_1.left_vertices.tolist())

        self.assertEqual(3, len(self.lanelet_1.right_vertices))
        self.assertEqual([[0., 0.], [1., 0.], [2., 0.]], self.lanelet_1.right_vertices.tolist())

        self.lanelet_1.left_vertices = np.array([[0., 1.], [0.5, 1.], [1., 1.], [1.5, 1.], [2., 1.]])

        self.lanelet_repairer.repair_same_vertices_size((1,))

        self.assertEqual(5, len(self.lanelet_1.right_vertices))
        self.assertEqual([[0., 0.], [0.5, 0.], [1., 0.], [1.5, 0.], [2., 0.]], self.lanelet_1.right_vertices.tolist())

    def test_existence_left_adj(self):
        self.lanelet_1.adj_left = 2

        self.lanelet_repairer.repair_existence_left_adj((1,))

        self.assertEqual(None, self.lanelet_1.adj_left)

    def test_existence_right_adj(self):
        self.lanelet_1.adj_right = 2

        self.lanelet_repairer.repair_existence_right_adj((1,))

        self.assertEqual(None, self.lanelet_1.adj_right)

    def test_existence_predecessor(self):
        self.lanelet_1.predecessor.append(2)

        self.lanelet_repairer.repair_existence_predecessor((1, 2))

        self.assertEqual([], self.lanelet_1.predecessor)

    def test_existence_successor(self):
        self.lanelet_1.successor.append(2)

        self.lanelet_repairer.repair_existence_successor((1, 2))

        self.assertEqual([], self.lanelet_1.successor)

    def test_connections_predecessor(self):
        self.lanelet_2.left_vertices = np.array([[-2., 1.], [-1., 1.], [0., 1.1]])

        self.lanelet_repairer.repair_connections_predecessor((1, 2))

        self.assertEqual(self.lanelet_1.left_vertices[0].tolist(), self.lanelet_2.left_vertices[2].tolist())

        self.lanelet_2.right_vertices = np.array([[-2., 0.], [-1., 0.], [0., 0.1]])

        self.lanelet_repairer.repair_connections_predecessor((1, 2))

        self.assertEqual(self.lanelet_1.right_vertices[0].tolist(), self.lanelet_2.right_vertices[2].tolist())

    def test_connections_successor(self):
        self.lanelet_2.left_vertices = np.array([[2., 0.9], [3., 1.], [4., 1.]])

        self.lanelet_repairer.repair_connections_successor((1, 2))

        self.assertEqual(self.lanelet_1.left_vertices[2].tolist(), self.lanelet_2.left_vertices[0].tolist())

        self.lanelet_2.right_vertices = np.array([[2., -0.05], [3., 0], [4., 0]])

        self.lanelet_repairer.repair_connections_successor((1, 2))

        self.assertEqual(self.lanelet_1.right_vertices[2].tolist(), self.lanelet_2.right_vertices[0].tolist())

    def test_polylines_left_same_dir_parallel_adj(self):
        self.lanelet_2.right_vertices = np.array([[0., 1.], [1., 0.9], [2., 1.]])

        self.lanelet_repairer.repair_polylines_left_same_dir_parallel_adj((1, 2))

        self.assertEqual(self.lanelet_1.left_vertices.tolist(), self.lanelet_2.right_vertices.tolist())

    def test_polylines_left_opposite_dir_parallel_adj(self):
        self.lanelet_2.left_vertices = np.array([[2., 1.], [1., 0.9], [0., 1.2]])

        self.lanelet_repairer.repair_polylines_left_opposite_dir_parallel_adj((1, 2))

        self.assertEqual(self.lanelet_1.left_vertices.tolist(), self.lanelet_2.left_vertices.tolist()[::-1])

    def test_polylines_right_same_dir_parallel_adj(self):
        self.lanelet_2.left_vertices = np.array([[0.1, 0.], [1., 0.], [2., 0.]])

        self.lanelet_repairer.repair_polylines_right_same_dir_parallel_adj((1, 2))

        self.assertEqual(self.lanelet_1.right_vertices.tolist(), self.lanelet_2.left_vertices.tolist())

    def test_polylines_right_opposite_dir_parallel_adj(self):
        self.lanelet_2.right_vertices = np.array([[2., 0.], [1., 0.5], [0., 0.]])

        self.lanelet_repairer.repair_polylines_right_opposite_dir_parallel_adj((1, 2))

        self.assertEqual(self.lanelet_1.right_vertices.tolist(), self.lanelet_2.right_vertices.tolist()[::-1])

    def test_connections_left_merging_adj(self):
        self.lanelet_2.left_vertices = np.array([[0., 2.], [1., 1.5], [2., 1.1]])

        self.lanelet_repairer.repair_connections_left_merging_adj((1, 2))

        self.assertEqual(self.lanelet_1.left_vertices[2].tolist(), self.lanelet_2.left_vertices[2].tolist())

        self.lanelet_2.right_vertices = np.array([[0., 1.], [1., 0.5], [2., 0.1]])

        self.lanelet_repairer.repair_connections_left_merging_adj((1, 2))

        self.assertEqual(self.lanelet_1.right_vertices[2].tolist(), self.lanelet_2.right_vertices[2].tolist())

        self.lanelet_2.right_vertices = np.array([[0., 1.], [1., 0.5], [2., 0.1]])

        self.lanelet_repairer.repair_connections_left_merging_adj((1, 2))

        self.assertEqual(self.lanelet_1.left_vertices[0].tolist(), self.lanelet_2.right_vertices[0].tolist())

    def test_connections_right_merging_adj(self):
        self.lanelet_2.left_vertices = np.array([[0.1, 0.], [1., 0.5], [2., 1.]])

        self.lanelet_repairer.repair_connections_right_merging_adj((1, 2))

        self.assertEqual(self.lanelet_1.right_vertices[0].tolist(), self.lanelet_2.left_vertices[0].tolist())

        self.lanelet_2.left_vertices = np.array([[0., 0.], [1., 0.5], [2., 1.5]])

        self.lanelet_repairer.repair_connections_right_merging_adj((1, 2))

        self.assertEqual(self.lanelet_1.left_vertices[2].tolist(), self.lanelet_2.left_vertices[2].tolist())

        self.lanelet_2.right_vertices = np.array([[0., -1.], [1., -0.5], [2., 0.1]])

        self.lanelet_repairer.repair_connections_right_merging_adj((1, 2))

        self.assertEqual(self.lanelet_1.right_vertices[2].tolist(), self.lanelet_2.right_vertices[2].tolist())

    def test_connections_left_forking_adj(self):
        self.lanelet_2.left_vertices = np.array([[0., 0.9], [1., 1.5], [2., 2.]])

        self.lanelet_repairer.repair_connections_left_forking_adj((1, 2))

        self.assertEqual(self.lanelet_1.left_vertices[0].tolist(), self.lanelet_2.left_vertices[0].tolist())

        self.lanelet_2.right_vertices = np.array([[0., 0.], [1., 0.5], [1.9, 1.]])

        self.lanelet_repairer.repair_connections_left_forking_adj((1, 2))

        self.assertEqual(self.lanelet_1.left_vertices[2].tolist(), self.lanelet_2.right_vertices[2].tolist())

        self.lanelet_2.right_vertices = np.array([[0., -0.1], [1., 0.5], [2., 1.]])

        self.lanelet_repairer.repair_connections_left_forking_adj((1, 2))

        self.assertEqual(self.lanelet_1.right_vertices[0].tolist(), self.lanelet_2.right_vertices[0].tolist())

    def test_connections_right_forking_adj(self):
        self.lanelet_2.right_vertices = np.array([[0., 0.1], [1., -0.5], [2., -1.]])

        self.lanelet_repairer.repair_connections_right_forking_adj((1, 2))

        self.assertEqual(self.lanelet_1.right_vertices[0].tolist(), self.lanelet_2.right_vertices[0].tolist())

        self.lanelet_2.left_vertices = np.array([[0., 1.1], [1., 0.5], [2., 0.]])

        self.lanelet_repairer.repair_connections_right_forking_adj((1, 2))

        self.assertEqual(self.lanelet_1.left_vertices[0].tolist(), self.lanelet_2.left_vertices[0].tolist())

        self.lanelet_2.left_vertices = np.array([[0., 1.], [1., 0.5], [2.3, 0.]])

        self.lanelet_repairer.repair_connections_right_forking_adj((1, 2))

        self.assertEqual(self.lanelet_1.right_vertices[2].tolist(), self.lanelet_2.left_vertices[2].tolist())

    def test_potential_predecessor(self):
        self.lanelet_repairer.repair_potential_predecessor((1, 2))

        self.assertEqual([2], self.lanelet_1.predecessor)

    def test_potential_successor(self):
        self.lanelet_repairer.repair_potential_successor((1, 2))

        self.assertEqual([2], self.lanelet_1.successor)

    def test_potential_left_same_dir_parallel_adj(self):
        self.lanelet_repairer.repair_potential_left_same_dir_parallel_adj((1, 2))

        self.assertEqual(2, self.lanelet_1.adj_left)
        self.assertEqual(True, self.lanelet_1.adj_left_same_direction)

    def test_potential_left_opposite_dir_parallel_adj(self):
        self.lanelet_repairer.repair_potential_left_opposite_dir_parallel_adj((1, 2))

        self.assertEqual(2, self.lanelet_1.adj_left)
        self.assertEqual(False, self.lanelet_1.adj_left_same_direction)

    def test_potential_right_same_dir_parallel_adj(self):
        self.lanelet_repairer.repair_potential_right_same_dir_parallel_adj((1, 2))

        self.assertEqual(2, self.lanelet_1.adj_right)
        self.assertEqual(True, self.lanelet_1.adj_right_same_direction)

    def test_potential_right_opposite_dir_parallel_adj(self):
        self.lanelet_repairer.repair_potential_right_opposite_dir_parallel_adj((1, 2))

        self.assertEqual(2, self.lanelet_1.adj_right)
        self.assertEqual(False, self.lanelet_1.adj_right_same_direction)

    def test_potential_left_merging_adj(self):
        self.lanelet_repairer.repair_potential_left_merging_adj((1, 2))

        self.assertEqual(2, self.lanelet_1.adj_left)
        self.assertEqual(True, self.lanelet_1.adj_left_same_direction)

    def test_potential_right_merging_adj(self):
        self.lanelet_repairer.repair_potential_right_merging_adj((1, 2))

        self.assertEqual(2, self.lanelet_1.adj_right)
        self.assertEqual(True, self.lanelet_1.adj_right_same_direction)

    def test_potential_left_forking_adj(self):
        self.lanelet_repairer.repair_potential_left_forking_adj((1, 2))

        self.assertEqual(2, self.lanelet_1.adj_left)
        self.assertEqual(True, self.lanelet_1.adj_left_same_direction)

    def test_potential_right_forking_adj(self):
        self.lanelet_repairer.repair_potential_right_forking_adj((1, 2))

        self.assertEqual(2, self.lanelet_1.adj_right)
        self.assertEqual(True, self.lanelet_1.adj_right_same_direction)

    def test_polylines_intersection(self):
        self.lanelet_1.right_vertices = np.array([[0., 0.], [1., 2.], [2., 0.]])

        self.lanelet_repairer.repair_polylines_intersection((1,))

        self.assertEqual([[0., 1.], [1., 2.], [2., 1.]], self.lanelet_1.left_vertices.tolist())
        self.assertEqual([[0., 0.], [1., 1.], [2., 0.]], self.lanelet_1.right_vertices.tolist())

    def test_left_self_intersection(self):
        self.lanelet_1.left_vertices = np.array([[-2., -2.], [-1., -1.], [0.5, 0.], [-0.5, 0], [1., -1.], [2., -2.]])
        self.lanelet_repairer.repair_left_self_intersection((1,))
        self.assertEqual([[-2., -2.], [-1.3171572875253812, -1.3171572875253812], [-0.4828427124746193, -1.0],
                          [0.4828427124746184, -1.], [1.3171572875253807, -1.3171572875253807],
                          [2., -2.]], self.lanelet_1.left_vertices.tolist())

        self.lanelet_1.left_vertices = np.array([[0.0, 1.0], [0.5, 1.0], [0.25, 1.0], [0.75, 1.0]])
        self.lanelet_repairer.repair_left_self_intersection((1,))
        self.assertEqual([[0.0, 1.0], [0.16666666666666669, 1.], [0.33333333333333337, 1.0], [0.75, 1.0]],
                         self.lanelet_1.left_vertices.tolist())

        self.lanelet_1.left_vertices = np.array([[0.0, 1.0], [0.5, 1.0], [0.5, 1.0], [0.75, 1.0]])
        self.lanelet_repairer.repair_left_self_intersection((1,))
        self.assertEqual([[0.0, 1.0], [0.25, 1.], [0.5, 1.0], [0.75, 1.0]],
                         self.lanelet_1.left_vertices.tolist())

    def test_right_self_intersection(self):
        self.lanelet_1.right_vertices = np.array([[0., 0.], [1., 0.], [2., 0.], [3., 0], [2., 0.5],
                                                 [2., -0.5], [3, -0.5], [4, -0.5]])
        self.lanelet_repairer.repair_right_self_intersection((1,))
        self.assertEqual([[0.0, 0.0], [0.5882905698214136, 0.0], [1.1579389727142977, -0.0789694863571489],
                          [1.6841220545714046, -0.3420610272857023], [2.2351282905357595, -0.5],
                          [2.8234188603571733, -0.5], [3.4117094301785866, -0.5],
                          [4.0, -0.5]], self.lanelet_1.right_vertices.tolist())

        self.lanelet_1.right_vertices = np.array([[0.0, 1.0], [0.5, 1.0], [0.5, 1.0], [0.75, 1.0]])
        self.lanelet_repairer.repair_right_self_intersection((1,))
        self.assertEqual([[0.0, 1.0], [0.25, 1.0], [0.5, 1.0], [0.75, 1.0]], self.lanelet_1.right_vertices.tolist())

        self.lanelet_1.right_vertices = np.array([[0.0, 1.0], [0.5, 1.0], [0.25, 1.0], [0.75, 1.0]])
        self.lanelet_repairer.repair_right_self_intersection((1,))
        self.assertEqual([[0.0, 1.0], [0.16666666666666669, 1.0], [0.33333333333333337, 1.0], [0.75, 1.0]],
                         self.lanelet_1.right_vertices.tolist())

    def test_lanelet_types_combination(self):
        pass

    def test_non_followed_composable_lanelets(self):
        self.lanelet_2.left_vertices = np.array([[2., 1.], [3., 1.], [4., 1.]])
        self.lanelet_2.right_vertices = np.array([[2., 0.], [3., 0.], [4., 0.]])

        self.lanelet_1.successor = [2]
        self.lanelet_2.predecessor = [1]

        self.lanelet_repairer.repair_non_followed_composable_lanelets((1, 2))

        self.assertEqual(1, len(self.network.lanelets))
        self.assertEqual(12, self.network.lanelets[0].lanelet_id)

    def test_referenced_intersecting_lanelets(self):
        pass

    def test_existence_traffic_signs(self):
        self.lanelet_1.add_traffic_sign_to_lanelet(9)

        self.lanelet_repairer.repair_existence_traffic_signs((1, 9))

        self.assertEqual(set(), self.lanelet_1.traffic_signs)

    def test_existence_traffic_lights(self):
        self.lanelet_1.add_traffic_light_to_lanelet(9)

        self.lanelet_repairer.repair_existence_traffic_lights((1, 9))

        self.assertEqual(set(), self.lanelet_1.traffic_lights)

    def test_existence_stop_line_traffic_signs(self):
        stop_line = StopLine(np.array([0., 0.]), np.array([1., 1.]), LineMarking.NO_MARKING, {9}, set())
        self.lanelet_1.stop_line = stop_line

        self.lanelet_repairer.repair_existence_stop_line_traffic_signs((1, 9))

        self.assertEqual(set(), self.lanelet_1.stop_line.traffic_sign_ref)

    def test_existence_stop_line_traffic_lights(self):
        stop_line = StopLine(np.array([0., 0.]), np.array([1., 1.]), LineMarking.NO_MARKING, set(), {9})
        self.lanelet_1.stop_line = stop_line

        self.lanelet_repairer.repair_existence_stop_line_traffic_lights((1, 9))

        self.assertEqual(set(), self.lanelet_1.stop_line.traffic_light_ref)

    def test_included_stop_line_traffic_signs(self):
        stop_line = StopLine(np.array([0., 0.]), np.array([1., 1.]), LineMarking.NO_MARKING, {1, 2}, set())
        self.lanelet_1.stop_line = stop_line

        self.lanelet_1.traffic_signs = {1, 3}

        self.lanelet_repairer.repair_included_stop_line_traffic_signs((1, 2))

        self.assertEqual({1, 3}, self.lanelet_1.traffic_signs)

    def test_zero_or_two_points_stop_line(self):
        stop_line = StopLine(np.array([0., 0.]), None, LineMarking.NO_MARKING, set(), set())
        self.lanelet_1.stop_line = stop_line

        self.lanelet_repairer.repair_zero_or_two_points_stop_line((1,))

        self.assertEqual(None, self.lanelet_1.stop_line.start)
        self.assertEqual(None, self.lanelet_1.stop_line.end)

    def test_included_stop_line_traffic_lights(self):
        stop_line = StopLine(np.array([0., 0.]), np.array([1., 1.]), LineMarking.NO_MARKING, set(), {1, 2})
        self.lanelet_1.stop_line = stop_line

        self.lanelet_1.traffic_lights = {1, 3}

        self.lanelet_repairer.repair_included_stop_line_traffic_lights((1, 2))

        self.assertEqual({1, 2, 3}, self.lanelet_1.traffic_lights)

    def test_stop_line_points_on_polylines(self):
        stop_line = StopLine(np.array([2., 1.5]), np.array([2., -0.5]), LineMarking.NO_MARKING, set(), set())
        self.lanelet_1.stop_line = stop_line

        self.lanelet_repairer.repair_stop_line_points_on_polylines((1,))

        self.assertEqual([2., 1.], stop_line.start.tolist())
        self.assertEqual([2., 0.], stop_line.end.tolist())


class TestTrafficSignRepairing(unittest.TestCase):
    """
    The class tests the repairing of traffic sign elements.
    """

    def setUp(self) -> None:
        lanelet = Lanelet(np.array([[0., 1.], [1., 1.]]), np.array([[0., 0.5], [1., 0.5]]),
                          np.array([[0., 0.], [1., 0.]]), 1)

        traffic_sign_element = TrafficSignElement(TrafficSignIDGermany.TOWN_SIGN, ['Munich'])
        self.traffic_sign = TrafficSign(1, [traffic_sign_element], {1}, np.array([0., 0.]))

        self.network = LaneletNetwork()
        self.network.add_lanelet(lanelet)
        self.network.add_traffic_sign(self.traffic_sign, {1})
        self.scenario_id = ScenarioID()
        self.traffic_sign_repairer = TrafficSignRepairing(self.network)

    def test_at_least_one_traffic_sign_element(self):
        self.traffic_sign.traffic_sign_elements.clear()

        self.traffic_sign_repairer.repair_at_least_one_traffic_sign_element((1,))

        self.assertEqual([], self.network.traffic_signs)

    def test_referenced_traffic_sign(self):
        lanelet = self.network.find_lanelet_by_id(1)
        lanelet.traffic_signs.remove(1)

        self.traffic_sign_repairer.repair_referenced_traffic_sign((1,))

        self.assertEqual([], self.network.traffic_signs)

    def test_given_additional_value(self):
        traffic_sign_element = TrafficSignElement(TrafficSignIDZamunda.MAX_SPEED, [])
        self.traffic_sign.traffic_sign_elements = [traffic_sign_element]

        self.traffic_sign_repairer.repair_given_additional_value(
                (1, hash(TrafficSignIDZamunda.MAX_SPEED.name.lower())))

        self.assertEqual(['120'], self.traffic_sign.traffic_sign_elements[0].additional_values)

    def test_valid_additional_value_speed_sign(self):
        traffic_sign_element = TrafficSignElement(TrafficSignIDGermany.MAX_SPEED, ['30', 'Munich'])
        self.traffic_sign.traffic_sign_elements = [traffic_sign_element]

        self.traffic_sign_repairer.repair_valid_additional_value_speed_sign(
                (1, hash(TrafficSignIDGermany.MAX_SPEED.name.lower())))

        self.assertEqual(['30'], self.traffic_sign.traffic_sign_elements[0].additional_values)

    def test_maximal_distance_from_lanelet(self):
        self.traffic_sign.position = np.array([0., -2.])

        self.traffic_sign_repairer.repair_maximal_distance_from_lanelet((1,))

        self.assertEqual([0., -0.5], self.traffic_sign.position.tolist())


class TestTrafficLightRepairing(unittest.TestCase):
    """
    The class tests the repairing of traffic light elements.
    """

    def setUp(self) -> None:
        lanelet = Lanelet(np.array([[0., 1.], [1., 1.]]), np.array([[0., 0.5], [1., 0.5]]),
                          np.array([[0., 0.], [1., 0.]]), 1)

        traffic_cycle_element_0 = TrafficLightCycleElement(TrafficLightState.RED, 10)
        traffic_cycle_element_1 = TrafficLightCycleElement(TrafficLightState.YELLOW, 5)
        traffic_cycle_element_2 = TrafficLightCycleElement(TrafficLightState.GREEN, 10)

        self.traffic_light = TrafficLight(1, np.array([0.0, 0.0]),
                TrafficLightCycle([traffic_cycle_element_0, traffic_cycle_element_1, traffic_cycle_element_2]))

        self.network = LaneletNetwork()
        self.network.add_lanelet(lanelet)
        self.network.add_traffic_light(self.traffic_light, {1})
        self.scenario_id = ScenarioID()
        self.traffic_light_repairer = TrafficLightRepairing(self.network)

    def test_at_least_one_cycle_element(self):
        self.traffic_light.cycle = []

        self.traffic_light_repairer.repair_at_least_one_cycle_element((1,))

        self.assertEqual([], self.network.traffic_lights)

    def test_traffic_light_per_incoming(self):
        pass

    def test_referenced_traffic_light(self):
        self.traffic_light_repairer.repair_referenced_traffic_light((1,))

        self.assertEqual([], self.network.traffic_lights)

    def test_non_zero_duration(self):
        traffic_cycle_element_1 = self.traffic_light.traffic_light_cycle.cycle_elements[0]
        traffic_cycle_element_1.duration = -10

        self.traffic_light_repairer.repair_non_zero_duration((1,))

        self.assertEqual(30, traffic_cycle_element_1.duration)

    def test_unique_state_in_cycle(self):
        traffic_cycle_element_3 = TrafficLightCycleElement(TrafficLightState.RED, 8)
        self.traffic_light.traffic_light_cycle.cycle_elements.append(traffic_cycle_element_3)

        self.traffic_light_repairer.repair_unique_state_in_cycle((1, hash(TrafficLightState.RED)))

        self.assertEqual([TrafficLightState.RED, TrafficLightState.YELLOW, TrafficLightState.GREEN],
                         [cycle_e.state for cycle_e in self.traffic_light.traffic_light_cycle.cycle_elements])

    def test_cycle_state_combinations(self):
        traffic_cycle_element_0 = TrafficLightCycleElement(TrafficLightState.RED_YELLOW, 10)
        self.traffic_light.traffic_light_cycle.cycle_elements[0] = traffic_cycle_element_0

        self.traffic_light_repairer.repair_cycle_state_combinations((1,))

        self.assertEqual([(TrafficLightState.RED, 30), (TrafficLightState.RED_YELLOW, 3),
                          (TrafficLightState.GREEN, 30), (TrafficLightState.YELLOW, 3)],
                         [(cycle_e.state, cycle_e.duration) for cycle_e in
                          self.traffic_light.traffic_light_cycle.cycle_elements])

# class TestIntersectionRepairing(unittest.TestCase):
#     """
#     The class tests the repairing of intersection elements.
#     """
#
#     def setUp(self) -> None:
#         lanelet_0 = Lanelet(np.array([[0., 1.], [1., 1.]]), np.array([[0., 0.5], [1., 0.5]]),
#                             np.array([[0., 0.], [1., 0.]]), 1)
#         lanelet_1 = Lanelet(np.array([[2., 2.], [2., 1.]]), np.array([[2., 1.5], [1., 1.5]]),
#                             np.array([[1., 2.], [1., 1.]]), 2)
#
#         incoming_element_0 = IncomingGroup(3, incoming_lanelets={1})
#         incoming_element_1 = IncomingGroup(4, incoming_lanelets={2})
#
#         self.intersection = Intersection(5, incomings=[incoming_element_0, incoming_element_1])
#
#         self.network = LaneletNetwork()
#         self.network.add_lanelet(lanelet_0)
#         self.network.add_lanelet(lanelet_1)
#         self.network.add_intersection(self.intersection)
#         self.scenario_id = ScenarioID()
#         self.intersection_repairer = IntersectionRepairing(self.network)
#
#     def test_at_least_two_incoming_elements(self):
#         self.intersection_repairer.repair_at_least_two_incoming_elements((5,))
#
#         self.assertEqual(0, len(self.network.intersections))
#
#     def test_at_least_one_incoming_lanelet(self):
#         self.intersection_repairer.repair_at_least_one_incoming_lanelet((5, 3))
#
#         self.assertEqual(1, len(self.intersection.map_incoming_lanelets))
#         self.assertEqual(4, self.intersection.map_incoming_lanelets.get(2).incoming_id)
#
#     def test_existence_is_left_of(self):
#         incoming_element = self.intersection.incomings[0]
#         incoming_element.left_of = 9
#
#         self.intersection_repairer.repair_existence_is_left_of((5, 3))
#
#         self.assertEqual(None, incoming_element.left_of)
#
#     def test_existence_incoming_lanelets(self):
#         incoming_element = self.intersection.incomings[0]
#
#         self.intersection_repairer.repair_existence_incoming_lanelets((5, 3, 1))
#
#         self.assertEqual(0, len(incoming_element.incoming_lanelets))


if __name__ == '__main__':
    unittest.main()
