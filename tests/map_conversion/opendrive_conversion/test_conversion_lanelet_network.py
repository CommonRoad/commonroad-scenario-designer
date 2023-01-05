import unittest

import numpy as np
import crdesigner.map_conversion.opendrive.opendrive_conversion.conversion_lanelet_network
from crdesigner.map_conversion.opendrive.opendrive_conversion.conversion_lanelet_network import \
    ConversionLaneletNetwork, ConversionLanelet, _JoinSplitTarget, _JoinSplitPair
from commonroad.scenario.lanelet import LaneletNetwork, StopLine
from commonroad.scenario.traffic_sign import TrafficLight, TrafficSign
from commonroad.scenario.intersection import Intersection, IntersectionIncomingElement
from commonroad.scenario.lanelet import LaneletType
from crdesigner.map_conversion.opendrive.opendrive_conversion.plane_elements.plane_group import \
    ParametricLane, ParametricLaneGroup
from crdesigner.map_conversion.opendrive.opendrive_conversion.plane_elements.plane import ParametricLaneBorderGroup, \
    Border
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadPlanView import PlanView
from typing import List
from crdesigner.configurations.get_configs import get_configs
from crdesigner.map_conversion.common.utils import generate_unique_id


def init_lanelet_from_id(identifier) -> ConversionLanelet:
    lanelet = ConversionLanelet(None, np.array([[0, 1], [1, 1], [2, 1]]), np.array([[0, 0], [1, 0], [2, 0]]),
                                np.array([[0, -1], [1, -1], [2, -1]]), 1)
    lanelet.lanelet_id = identifier
    return lanelet


def init_lanelet_empty_vertices_from_id(plane_group, id) -> ConversionLanelet:
    lanelet = ConversionLanelet(plane_group, np.array([[0, 0], [0, 0]]), np.array([[0, 0], [0, 0]]),
                                np.array([[0, 0], [0, 0]]), id)
    return lanelet


def add_lanelets_to_network(network: ConversionLaneletNetwork,  lanelets: List[ConversionLanelet]):
    for la in lanelets:
        network.add_lanelet(la)


class TestConversionLanelet(unittest.TestCase):

    def setUp(self) -> None:
        generate_unique_id(0) # reset ID counter

    def test_convert_to_new_lanelet_id(self):
        ids_assigned = {'69.0.-1.-1': 5, '89.0.4.-1': 6, '71.0.1.-1': 7, '71.0.-3.-1': 8}
        old_lanelet_id = '71.0.-3.-1'
        true_new_id = ids_assigned[old_lanelet_id]
        self.assertEqual(true_new_id, crdesigner.map_conversion.opendrive.opendrive_conversion
                          .conversion_lanelet_network.convert_to_new_lanelet_id(old_lanelet_id, ids_assigned))

    def test_init(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        self.assertTrue(issubclass(ConversionLaneletNetwork, LaneletNetwork))
        self.assertDictEqual({}, conversion_lanelet_network.old_lanelet_ids())

    def test_old_lanelet_ids(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        conversion_lanelet_network._old_lanelet_ids = {'69.0.-1.-1': 5, '89.0.4.-1': 6}
        self.assertDictEqual({'69.0.-1.-1': 5, '89.0.4.-1': 6}, conversion_lanelet_network.old_lanelet_ids())

    def test_remove_lanelet(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        conversion_lanelet_1 = init_lanelet_from_id('79.0.-3.-1')
        conversion_lanelet_2 = init_lanelet_from_id('89.0.4.-1')

        add_lanelets_to_network(conversion_lanelet_network, [conversion_lanelet_1, conversion_lanelet_2])
        # test without removing references
        conversion_lanelet_network.remove_lanelet('89.0.4.-1')
        lanelets = [lanelet.lanelet_id for lanelet in conversion_lanelet_network.lanelets]
        true_lanelets = ['79.0.-3.-1']
        self.assertListEqual(true_lanelets, lanelets)

        # test with removing references of lanelet 1:
        conversion_lanelet_1.predecessor.append('86.0.-1.-1')
        conversion_lanelet_1.successor.append('82.0.-3.-1')
        add_lanelets_to_network(conversion_lanelet_network, [init_lanelet_from_id('82.0.-3.-1'),
                                                             init_lanelet_from_id('86.0.-1.-1')])

        conversion_lanelet_network.remove_lanelet('82.0.-3.-1', True)
        conversion_lanelet_network.remove_lanelet('86.0.-1.-1', True)
        # expected result: Lanelets with ID 82.0.-3.-1 and 86.0.-1.-1 are removed
        # plus the references to those lanelets of lanelet with id '79.0.-3.-1'
        lanelets = [lanelet.lanelet_id for lanelet in conversion_lanelet_network.lanelets]
        true_lanelets = ['79.0.-3.-1']
        self.assertListEqual(true_lanelets, lanelets)
        self.assertListEqual([[]], [lanelet.successor for lanelet in conversion_lanelet_network.lanelets])
        self.assertListEqual([[]], [lanelet.predecessor for lanelet in conversion_lanelet_network.lanelets])

    def test_find_lanelet_by_id(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        conversion_lanelet_1 = init_lanelet_from_id('79.0.-3.-1')

        add_lanelets_to_network(conversion_lanelet_network, [conversion_lanelet_1])

        self.assertEqual('79.0.-3.-1', conversion_lanelet_network.find_lanelet_by_id('79.0.-3.-1').lanelet_id)

        self.assertIsNone(conversion_lanelet_network.find_lanelet_by_id('foo'))

    def test_find_traffic_light_by_id(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        t1 = TrafficLight(100, [])
        t2 = TrafficLight(101, [])
        traffic_light_dict = {100: t1, 101: t2}
        conversion_lanelet_network._traffic_lights = traffic_light_dict
        self.assertEqual(t1, conversion_lanelet_network.find_traffic_light_by_id(100))
        self.assertEqual(t2, conversion_lanelet_network.find_traffic_light_by_id(101))

    def test_find_traffic_sign_by_id(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)

        sign1 = TrafficSign(0, [], set(), np.array([4.9, -0.1]), virtual=False)
        sign2 = TrafficSign(1, [], set(), np.array([0.1, 4.9]), virtual=False)
        sign3 = TrafficSign(2, [], set(), np.array([4.0, 4.0]), virtual=False)
        traffic_sign_dict = {0: sign1, 1: sign2, 2: sign3}
        conversion_lanelet_network._traffic_signs = traffic_sign_dict
        self.assertEqual(sign1, conversion_lanelet_network.find_traffic_sign_by_id(0))
        self.assertEqual(sign2, conversion_lanelet_network.find_traffic_sign_by_id(1))
        self.assertEqual(sign3, conversion_lanelet_network.find_traffic_sign_by_id(2))

    def test_convert_all_lanelet_ids(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        lanelet1 = init_lanelet_from_id('69.0.-1.-1')
        lanelet1.predecessor.append('89.0.4.-1')
        lanelet1.successor.append('71.0.1.-1')

        lanelet2 = init_lanelet_from_id('71.0.1.-1')
        lanelet2.predecessor.append('69.0.-1.-1')
        lanelet2.predecessor.append('72.0.-1.-1')
        lanelet2.predecessor.append('87.0.-1.-1')
        lanelet2.successor.append('89.0.3.-1')
        lanelet2.successor.append('89.0.2.-1')
        lanelet2.successor.append('89.0.4.-1')

        add_lanelets_to_network(conversion_lanelet_network, [lanelet1, lanelet2])

        conversion_lanelet_network.convert_all_lanelet_ids()

        new_lanelet_1 = conversion_lanelet_network.lanelets[0]
        new_lanelet_2 = conversion_lanelet_network.lanelets[1]

        self.assertEqual(1, new_lanelet_1.lanelet_id)
        self.assertEqual([2], new_lanelet_1.predecessor)
        self.assertEqual([3], new_lanelet_1.successor)
        self.assertEqual(3, new_lanelet_2.lanelet_id)
        self.assertEqual([1, 4, 5], new_lanelet_2.predecessor)
        self.assertEqual([6, 7, 2], new_lanelet_2.successor)

    def test_prune_network(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)

        plane_group = ParametricLaneGroup()
        inner_border = Border()
        inner_border.width_coefficients.append([5.0, 0, 0, 0])
        inner_border.width_coefficient_offsets.append(0.0)
        outer_border = Border()
        outer_border.width_coefficients.append([5.0, 0, 0, 0])
        outer_border.width_coefficient_offsets.append(0.0)
        plane_border_group = ParametricLaneBorderGroup(inner_border, 0.0, outer_border, 0.0)
        parametric_lane = ParametricLane('0', 'driving', plane_border_group, None, None, None)
        plane_group.parametric_lanes.append(parametric_lane)

        lanelet_1 = init_lanelet_empty_vertices_from_id(plane_group, '69.0.-1.-1')
        lanelet_2 = init_lanelet_empty_vertices_from_id(plane_group, '69.0.-3.-1')
        lanelet_3 = init_lanelet_empty_vertices_from_id(plane_group, '71.0.-1.-1')
        lanelet_4 = init_lanelet_empty_vertices_from_id(plane_group, '72.0.-1.-1')

        lanelet_1.adj_left = '100.0.0.0'
        lanelet_2.adj_right = '101.0.0.0'
        lanelet_3.predecessor = ['69.0.-1.-1', '200.0.0.0']
        lanelet_4.successor = ['72.0.-1.-1', '201.0.0.0']

        add_lanelets_to_network(conversion_lanelet_network, [lanelet_1, lanelet_2, lanelet_3, lanelet_4])

        conversion_lanelet_network.prune_network()

        self.assertIsNone(conversion_lanelet_network.find_lanelet_by_id('69.0.-1.-1').adj_left)
        self.assertIsNone(conversion_lanelet_network.find_lanelet_by_id('69.0.-3.-1').adj_right)
        self.assertListEqual(['69.0.-1.-1'], conversion_lanelet_network.find_lanelet_by_id('71.0.-1.-1').predecessor)
        self.assertListEqual(['72.0.-1.-1'], conversion_lanelet_network.find_lanelet_by_id('72.0.-1.-1').successor)

    def test_delete_zero_width_parametric_lane(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        plane_group = ParametricLaneGroup()
        plane_group2 = ParametricLaneGroup()

        inner_border = Border()
        inner_border.width_coefficients.append([0, 0, 0, 0])
        inner_border.width_coefficient_offsets.append(0.0)
        outer_border = Border()
        outer_border.width_coefficients.append([0, 0, 0, 0])
        outer_border.width_coefficient_offsets.append(0.0)
        plane_border_group = ParametricLaneBorderGroup(inner_border, 0.0, outer_border, 0.0)

        inner_border_2 = Border()
        inner_border_2.width_coefficients.append([5.0, 0, 0, 0])
        inner_border_2.width_coefficient_offsets.append(0.0)
        outer_border_2 = Border()
        outer_border_2.width_coefficients.append([5.0, 0, 0, 0])
        outer_border_2.width_coefficient_offsets.append(0.0)
        plane_border_group_2 = ParametricLaneBorderGroup(inner_border_2, 0.0, outer_border_2, 0.0)

        parametric_lane = ParametricLane('69.0.-1.0', 'driving', plane_border_group, 26.5, None, 'right')
        parametric_lane2 = ParametricLane('70.0.1.-1', 'driving', plane_border_group_2, 26.5, None, 'right')

        plane_group.parametric_lanes.append(parametric_lane)
        plane_group2.parametric_lanes.append(parametric_lane2)
        conversion_lanelet = init_lanelet_empty_vertices_from_id(plane_group, 0)
        conversion_lanelet.adj_right = 1
        conversion_lanelet_adj_right = init_lanelet_empty_vertices_from_id(plane_group2, 1)

        add_lanelets_to_network(conversion_lanelet_network, [conversion_lanelet, conversion_lanelet_adj_right])

        conversion_lanelet_network.delete_zero_width_parametric_lanes()
        self.assertEqual(1, len(conversion_lanelet_network.lanelets))
        self.assertEqual(1, conversion_lanelet_network.lanelets[0].lanelet_id)

    def test_update_lanelet_id_references(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)

        lanelet_1 = init_lanelet_empty_vertices_from_id(None, '71.0.-1.-1')
        lanelet_1.predecessor.append('91.0.1.-1')
        lanelet_1.successor.append('76.0.-1.-1')
        lanelet_1.successor.append('77.0.-1.-1')
        lanelet_1.successor.append('81.0.-1.-1')
        lanelet_1.adj_left = '71.0.1.-1'
        lanelet_1.adj_right = '68.0.1.1'

        add_lanelets_to_network(conversion_lanelet_network, [lanelet_1])

        conversion_lanelet_network.update_lanelet_id_references('91.0.1.-1', '80.0.-1.-1')
        true_pred_1 = ['80.0.-1.-1']
        self.assertListEqual(true_pred_1, conversion_lanelet_network.find_lanelet_by_id('71.0.-1.-1').predecessor)

        conversion_lanelet_network.update_lanelet_id_references('81.0.-1.-1', '99.0.0.-3')
        true_succ_1 = ['76.0.-1.-1', '77.0.-1.-1', '99.0.0.-3']
        self.assertListEqual(true_succ_1, conversion_lanelet_network.find_lanelet_by_id('71.0.-1.-1').successor)

        conversion_lanelet_network.update_lanelet_id_references('71.0.1.-1', '100.0.0.-1')
        self.assertEqual('100.0.0.-1', conversion_lanelet_network.find_lanelet_by_id('71.0.-1.-1').adj_left)

        conversion_lanelet_network.update_lanelet_id_references('68.0.1.1', '102.0.0.-1')
        self.assertEqual('102.0.0.-1', conversion_lanelet_network.find_lanelet_by_id('71.0.-1.-1').adj_right)

    def test_concatenate_possible_lanelets(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        plane_group = ParametricLaneGroup()

        lanelet_1 = init_lanelet_empty_vertices_from_id(plane_group, '50.0.0.0')
        lanelet_1_succ = init_lanelet_empty_vertices_from_id(plane_group, '51.0.0.0')
        lanelet_1_right_adj = init_lanelet_empty_vertices_from_id(plane_group, '50.0.0.-1')
        lanelet_1_right_adj_succ = init_lanelet_empty_vertices_from_id(plane_group, '51.0.0.-1')
        lanelet_1_left_adj = init_lanelet_empty_vertices_from_id(plane_group, '50.0.0.1')
        lanelet_1_left_adj_succ = init_lanelet_empty_vertices_from_id(plane_group, '51.0.0.1')

        lanelet_1.successor = ['51.0.0.0']
        lanelet_1_succ.predecessor = ['50.0.0.0']
        lanelet_1_succ.adj_right = '51.0.0.-1'
        lanelet_1.adj_right = '50.0.0.-1'
        lanelet_1.adj_right_same_direction = True
        lanelet_1_left_adj.successor = ['51.0.0.1']
        lanelet_1_left_adj_succ.predecessor = ['50.0.0.1']
        lanelet_1.adj_left_same_direction = True

        lanelet_1_right_adj.successor = ['51.0.0.-1']
        lanelet_1_right_adj_succ.predecessor = ['50.0.0.-1']

        add_lanelets_to_network(conversion_lanelet_network, [lanelet_1, lanelet_1_succ, lanelet_1_right_adj,
                                                             lanelet_1_right_adj_succ, lanelet_1_left_adj,
                                                             lanelet_1_left_adj_succ])

        replacement_ids = conversion_lanelet_network.concatenate_possible_lanelets()
        self.assertDictEqual({'51.0.0.0': '50.0.0.0', '51.0.0.-1': '50.0.0.-1', '51.0.0.1': '50.0.0.1'},
                             replacement_ids)

    def test_concatenate_lanelet_pairs_group(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        plane_group = ParametricLaneGroup()

        left_vertices_1 = np.array([[0, 1], [1, 1]])
        center_vertices_1 = np.array([[0, 0], [1, 0]])
        right_vertices_1 = np.array([[0, -1], [1, -1]])
        left_vertices_2 = np.array([[1, 1], [2, 1]])
        center_vertices_2 = np.array([[1, 0], [2, 0]])
        right_vertices_2 = np.array([[1, -1], [2, -1]])

        lanelet_1 = ConversionLanelet(plane_group, left_vertices_1, center_vertices_1, right_vertices_1, '69.0.-3.-1')
        lanelet_2 = ConversionLanelet(plane_group, left_vertices_2, center_vertices_2, right_vertices_2, '71.0.3.-1')

        add_lanelets_to_network(conversion_lanelet_network, [lanelet_1, lanelet_2])

        lanelet_pairs = [('69.0.-3.-1', '71.0.3.-1')]

        new_lanelet_ids = conversion_lanelet_network._concatenate_lanelet_pairs_group(lanelet_pairs)
        self.assertDictEqual({'71.0.3.-1': '69.0.-3.-1'}, new_lanelet_ids)
        self.assertListEqual([[0, 0], [1, 0], [2, 0]], lanelet_1.center_vertices.tolist())
        self.assertListEqual([[0, 1], [1, 1], [2, 1]], lanelet_1.left_vertices.tolist())
        self.assertListEqual([[0, -1], [1, -1], [2, -1]], lanelet_1.right_vertices.tolist())

    def test_predecessor_is_neighbor_of_neighbors_predecessor(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)

        lanelet_1 = init_lanelet_empty_vertices_from_id(None, '50.0.0.0')
        lanelet_1_pred = init_lanelet_empty_vertices_from_id(None, '49.0.0.0')
        lanelet_1.predecessor = ['49.0.0.0']
        lanelet_1_pred.successor = ['50.0.0.0']

        add_lanelets_to_network(conversion_lanelet_network, [lanelet_1, lanelet_1_pred])

        self.assertTrue(conversion_lanelet_network.predecessor_is_neighbor_of_neighbors_predecessor(lanelet_1))

    def test_add_successors_to_lanelet(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        lanelet_1 = init_lanelet_empty_vertices_from_id(None, '50.0.0.0')
        lanelet_1_succ_1 = init_lanelet_empty_vertices_from_id(None, '51.0.0.-1')
        lanelet_1_succ_2 = init_lanelet_empty_vertices_from_id(None, '51.0.0.-2')

        add_lanelets_to_network(conversion_lanelet_network, [lanelet_1, lanelet_1_succ_1, lanelet_1_succ_2])

        conversion_lanelet_network.add_successors_to_lanelet(lanelet_1, ['51.0.0.-1', '51.0.0.-2'])
        self.assertListEqual(['51.0.0.-1', '51.0.0.-2'], lanelet_1.successor)
        self.assertListEqual(['50.0.0.0'], lanelet_1_succ_1.predecessor)
        self.assertListEqual(['50.0.0.0'], lanelet_1_succ_2.predecessor)

    def test_add_predecessors_to_lanelet(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        lanelet_1 = init_lanelet_empty_vertices_from_id(None, '50.0.0.0')
        lanelet_1_pred_1 = init_lanelet_empty_vertices_from_id(None, '49.0.0.-1')
        lanelet_1_pred_2 = init_lanelet_empty_vertices_from_id(None, '49.0.0.-2')

        add_lanelets_to_network(conversion_lanelet_network, [lanelet_1, lanelet_1_pred_1, lanelet_1_pred_2])

        conversion_lanelet_network.add_predecessors_to_lanelet(lanelet_1, ['49.0.0.-1', '49.0.0.-2'])
        self.assertListEqual(['49.0.0.-1', '49.0.0.-2'], lanelet_1.predecessor)
        self.assertListEqual(['50.0.0.0'], lanelet_1_pred_1.successor)
        self.assertListEqual(['50.0.0.0'], lanelet_1_pred_2.successor)

    def test_set_adjacent_left(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)

        lanelet_1 = init_lanelet_empty_vertices_from_id(None, '50.0.0.-2')
        lanelet_1_adj_left = init_lanelet_empty_vertices_from_id(None, '50.0.0.-1')

        add_lanelets_to_network(conversion_lanelet_network, [lanelet_1, lanelet_1_adj_left])

        self.assertFalse(conversion_lanelet_network.set_adjacent_left(lanelet_1, 'foo', True))
        conversion_lanelet_network.set_adjacent_left(lanelet_1, '50.0.0.-1', True)
        self.assertEqual(lanelet_1.adj_left, '50.0.0.-1')
        self.assertEqual(lanelet_1_adj_left.adj_right, '50.0.0.-2')
        self.assertTrue(lanelet_1_adj_left.adj_right_same_direction)
        conversion_lanelet_network.set_adjacent_left(lanelet_1, '50.0.0.-1', False)
        self.assertFalse(lanelet_1_adj_left.adj_left_same_direction)

    def test_set_adjacent_right(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)

        lanelet_1 = init_lanelet_empty_vertices_from_id(None, '50.0.0.1')
        lanelet_1_adj_right = init_lanelet_empty_vertices_from_id(None, '50.0.0.2')

        add_lanelets_to_network(conversion_lanelet_network, [lanelet_1, lanelet_1_adj_right])

        self.assertFalse(conversion_lanelet_network.set_adjacent_left(lanelet_1, 'foo', True))
        conversion_lanelet_network.set_adjacent_right(lanelet_1, '50.0.0.2', True)
        self.assertEqual(lanelet_1.adj_right, '50.0.0.2')
        self.assertEqual(lanelet_1_adj_right.adj_left, '50.0.0.1')
        self.assertTrue(lanelet_1_adj_right.adj_left_same_direction)
        conversion_lanelet_network.set_adjacent_right(lanelet_1, '50.0.0.2', False)
        self.assertFalse(lanelet_1_adj_right.adj_right_same_direction)

    def test_check_concatenation_potential(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)

        lanelet_1 = init_lanelet_empty_vertices_from_id(None, '50.0.0.0')
        lanelet_1_succ = init_lanelet_empty_vertices_from_id(None, '51.0.0.0')
        lanelet_1_right_adj = init_lanelet_empty_vertices_from_id(None, '50.0.0.-1')
        lanelet_1_right_adj_succ = init_lanelet_empty_vertices_from_id(None, '51.0.0.-1')
        lanelet_1_left_adj = init_lanelet_empty_vertices_from_id(None, '50.0.0.1')
        lanelet_1_left_adj_succ = init_lanelet_empty_vertices_from_id(None, '51.0.0.1')

        lanelet_1.successor = ['51.0.0.0']
        lanelet_1_succ.predecessor = ['50.0.0.0']
        lanelet_1_succ.adj_right = '51.0.0.-1'
        lanelet_1.adj_right = '50.0.0.-1'
        lanelet_1.adj_right_same_direction = True
        lanelet_1_left_adj.successor = ['51.0.0.1']
        lanelet_1_left_adj_succ.predecessor = ['50.0.0.1']
        lanelet_1.adj_left_same_direction = True

        lanelet_1_right_adj.successor = ['51.0.0.-1']
        lanelet_1_right_adj_succ.predecessor = ['50.0.0.-1']

        add_lanelets_to_network(conversion_lanelet_network, [lanelet_1, lanelet_1_succ, lanelet_1_right_adj,
                                                             lanelet_1_right_adj_succ, lanelet_1_left_adj,
                                                             lanelet_1_left_adj_succ])

        mergeable_lanelets = conversion_lanelet_network.check_concatenation_potential(lanelet_1, "left")
        self.assertListEqual(mergeable_lanelets, [('50.0.0.0', '51.0.0.0')])

        mergeable_lanelets = conversion_lanelet_network.check_concatenation_potential(lanelet_1, 'right')
        self.assertListEqual([('50.0.0.0', '51.0.0.0'), ('50.0.0.-1', '51.0.0.-1')], mergeable_lanelets)

    def test_successor_is_neighbor_of_neighbors_successor(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)

        lanelet_1 = init_lanelet_empty_vertices_from_id(None, '50.0.0.0')
        lanelet_1_succ = init_lanelet_empty_vertices_from_id(None, '51.0.0.0')
        lanelet_1_right_adj = init_lanelet_empty_vertices_from_id(None, '50.0.0.-1')
        lanelet_1_right_adj_succ = init_lanelet_empty_vertices_from_id(None, '51.0.0.-1')
        lanelet_1_left_adj = init_lanelet_empty_vertices_from_id(None, '50.0.0.1')
        lanelet_1_left_adj_succ = init_lanelet_empty_vertices_from_id(None, '51.0.0.1')

        lanelet_1.successor = ['51.0.0.0']
        lanelet_1_succ.predecessor = ['50.0.0.0']
        lanelet_1_succ.adj_right = '51.0.0.-1'
        lanelet_1.adj_right = '50.0.0.-1'
        lanelet_1.adj_right_same_direction = True
        lanelet_1_left_adj.successor = ['51.0.0.1']
        lanelet_1_left_adj_succ.predecessor = ['50.0.0.1']
        lanelet_1.adj_left_same_direction = True

        lanelet_1_right_adj.successor = ['51.0.0.-1']
        lanelet_1_right_adj_succ.predecessor = ['50.0.0.-1']

        add_lanelets_to_network(conversion_lanelet_network, [lanelet_1, lanelet_1_succ, lanelet_1_right_adj,
                                                             lanelet_1_right_adj_succ, lanelet_1_left_adj,
                                                             lanelet_1_left_adj_succ])

        self.assertTrue(conversion_lanelet_network.successor_is_neighbor_of_neighbors_successor(lanelet_1))

    def test_has_unique_pred_succ_relation(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        lanelet_1 = init_lanelet_empty_vertices_from_id(None, '69.0.-1.-1')

        self.assertFalse(conversion_lanelet_network.has_unique_pred_succ_relation(1, lanelet_1))
        self.assertFalse(conversion_lanelet_network.has_unique_pred_succ_relation(-1, lanelet_1))

        lanelet_1.predecessor = ['70.0.-1.-1', '71.0.-1.-1']
        lanelet_1.successor = ['71.0.0.1', '72.0.1.1']

        self.assertFalse(conversion_lanelet_network.has_unique_pred_succ_relation(1, lanelet_1))
        self.assertFalse(conversion_lanelet_network.has_unique_pred_succ_relation(-1, lanelet_1))

        lanelet_1.successor = ['100.0.0.1']
        lanelet_1.predecessor = ['200.0.-1.-1']
        lanelet_1_successor_nb = init_lanelet_empty_vertices_from_id(None, '100.0.0.1')
        lanelet_1_successor_nb.predecessor = ['69.0.-1.-1']
        add_lanelets_to_network(conversion_lanelet_network, [lanelet_1_successor_nb])

        self.assertTrue(conversion_lanelet_network.has_unique_pred_succ_relation(1, lanelet_1))

    def test_adj_right_consistent_nb(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        lanelet_1 = init_lanelet_empty_vertices_from_id(None, '50.0.1.-1')
        lanelet_1.successor = ['51.0.1.-1']
        lanelet_1.adj_right_same_direction = True
        lanelet_1.adj_right = '50.0.1.-2'

        lanelet_1_adj_right = init_lanelet_empty_vertices_from_id(None, '50.0.1.-2')
        lanelet_1_adj_right.successor = ['51.0.1.-2']
        lanelet_1_adj_right_succ = init_lanelet_empty_vertices_from_id(None, '51.0.1.-2')
        lanelet_1_adj_right_succ.predecessor = ['50.0.1.-2']

        lanelet_1_succ = init_lanelet_empty_vertices_from_id(None, '51.0.1.-1')
        lanelet_1_succ.adj_right = '51.0.1.-2'

        add_lanelets_to_network(conversion_lanelet_network, [lanelet_1, lanelet_1_succ, lanelet_1_adj_right,
                                                             lanelet_1_adj_right_succ])

        self.assertTrue(conversion_lanelet_network.adj_right_consistent_nb(lanelet_1))

    def test_adj_left_consistent_nb(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        lanelet_1 = init_lanelet_empty_vertices_from_id(None, '50.0.1.1')
        lanelet_1.successor = ['51.0.1.1']
        lanelet_1.adj_left_same_direction = True
        lanelet_1.adj_left = '50.0.1.2'

        lanelet_1_adj_left = init_lanelet_empty_vertices_from_id(None, '50.0.1.2')
        lanelet_1_adj_left.successor = ['51.0.1.2']
        lanelet_1_adj_left_succ = init_lanelet_empty_vertices_from_id(None, '51.0.1.2')
        lanelet_1_adj_left_succ.predecessor = ['50.0.1.2']
        lanelet_1_succ = init_lanelet_empty_vertices_from_id(None, '51.0.1.1')
        lanelet_1_succ.adj_left = '51.0.1.2'

        add_lanelets_to_network(conversion_lanelet_network, [lanelet_1, lanelet_1_succ, lanelet_1_adj_left,
                                                             lanelet_1_adj_left_succ])

        self.assertTrue(conversion_lanelet_network.adj_left_consistent_nb(lanelet_1))

    def test_combine_common_incoming_lanelets(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        intersection_map = {10: [100], 11: [None], 12: [None], 13: [None], 14: [101, 102, 103]}

        incoming_lanelet_1 = init_lanelet_empty_vertices_from_id(None, 10)
        incoming_lanelet_1_adj_right_1 = init_lanelet_empty_vertices_from_id(None, 11)
        incoming_lanelet_1_adj_right_2 = init_lanelet_empty_vertices_from_id(None, 12)
        incoming_lanelet_2 = init_lanelet_empty_vertices_from_id(None, 13)
        incoming_lanelet_3 = init_lanelet_empty_vertices_from_id(None, 14)
        incoming_lanelet_3_adj_left_1 = init_lanelet_empty_vertices_from_id(None, 15)
        incoming_lanelet_3_adj_left_2 = init_lanelet_empty_vertices_from_id(None, 16)
        incoming_lanelet_3_adj_left_3 = init_lanelet_empty_vertices_from_id(None, 17)

        incoming_lanelet_1.adj_right_same_direction = True
        incoming_lanelet_1.adj_right = 11
        incoming_lanelet_1_adj_right_1.adj_right = 12
        incoming_lanelet_1_adj_right_1.adj_right_same_direction = True

        incoming_lanelet_3.adj_left = 15
        incoming_lanelet_3.adj_left_same_direction = True
        incoming_lanelet_3_adj_left_1.adj_left = 16
        incoming_lanelet_3_adj_left_1.adj_left_same_direction = True
        incoming_lanelet_3_adj_left_2.adj_left = 17
        incoming_lanelet_3_adj_left_2.adj_left_same_direction = True

        add_lanelets_to_network(conversion_lanelet_network, [incoming_lanelet_1, incoming_lanelet_1_adj_right_1,
                                                             incoming_lanelet_1_adj_right_2, incoming_lanelet_2,
                                                             incoming_lanelet_3, incoming_lanelet_3_adj_left_1,
                                                             incoming_lanelet_3_adj_left_2,
                                                             incoming_lanelet_3_adj_left_3])

        self.assertListEqual([[10, 11], [11], [12], [13], [14]],
                             conversion_lanelet_network.combine_common_incoming_lanelets(intersection_map))

    def test_check_lanelet_type_for_successor_of_successor(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        intersection_map = {0: [1]}

        lanelet_1 = init_lanelet_empty_vertices_from_id(None, -1)
        lanelet_1.successor = [0]

        left_vertices = np.array([[453.90265159, 495.27523765], [455.77043119, 435.28374993],
                                  [456.37176199, 375.28599181]])
        right_vertices = np.array([[450.15269756, 495.25667099], [452.02047715, 435.26518327],
                                   [452.62180795, 375.26742514]])
        center_vertices = np.array([[452.02767457, 495.26595432], [453.89545417, 435.2744666],
                                    [454.49678497, 375.27670847]])

        lanelet_2 = ConversionLanelet(None, left_vertices, center_vertices, right_vertices, 0)
        lanelet_2.successor = [1]

        left_vertices_succ = np.array([[453.74916757, 526.27485758],
                                       [453.8259089,  510.77504756],
                                       [453.90265022, 495.27523754]])
        right_vertices_succ = np.array([[449.99921353, 526.25629114], [450.07595486, 510.75648111],
                                        [450.15269618, 495.25667109]])
        center_vertices_succ = np.array([[451.87419055, 526.26557436], [451.95093188, 510.76576434],
                                         [452.0276732,  495.26595431]])

        lanelet_2_succ = ConversionLanelet(None, left_vertices_succ, center_vertices_succ, right_vertices_succ, 1)

        add_lanelets_to_network(conversion_lanelet_network, [lanelet_2, lanelet_2_succ])

        conversion_lanelet_network.check_lanelet_type_for_successor_of_successor(lanelet_1, intersection_map)
        self.assertEqual({LaneletType.INTERSECTION, LaneletType.URBAN}, lanelet_2.lanelet_type)

    def test_check_if_lanelet_in_intersection(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        intersection_map = {0: [1]}

        left_vertices = np.array([[453.90265159, 495.27523765], [455.77043119, 435.28374993],
                                  [456.37176199, 375.28599181]])
        right_vertices = np.array([[450.15269756, 495.25667099], [452.02047715, 435.26518327],
                                   [452.62180795, 375.26742514]])
        center_vertices = np.array([[452.02767457, 495.26595432], [453.89545417, 435.2744666],
                                    [454.49678497, 375.27670847]])

        lanelet_1 = ConversionLanelet(None, left_vertices, center_vertices, right_vertices, 0)
        lanelet_1.successor = [1]

        left_vertices_succ = np.array([[453.74916757, 526.27485758],
                                       [453.8259089,  510.77504756],
                                       [453.90265022, 495.27523754]])
        right_vertices_succ = np.array([[449.99921353, 526.25629114], [450.07595486, 510.75648111],
                                        [450.15269618, 495.25667109]])
        center_vertices_succ = np.array([[451.87419055, 526.26557436], [451.95093188, 510.76576434],
                                         [452.0276732,  495.26595431]])

        lanelet_1_succ = ConversionLanelet(None, left_vertices_succ, center_vertices_succ, right_vertices_succ, 1)

        add_lanelets_to_network(conversion_lanelet_network, [lanelet_1, lanelet_1_succ])

        self.assertTrue(conversion_lanelet_network.check_if_lanelet_in_intersection(lanelet_1, intersection_map))

    def test_check_if_successor_is_intersecting(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)

        intersection_map = {0: [5]}
        successor_list = [101]

        lanelet = init_lanelet_empty_vertices_from_id(None, 0)
        lanelet.successor = [100]
        successor_lane_left_vertices = np.array([[457.49912055, 526.2934242], [457.54273532, 517.48444517],
                                                 [458.49583374, 511.7454143], [460.24058312, 509.69928856],
                                                 [462.69357582, 508.5976499], [465.38202077, 508.65282873],
                                                 [465.76946692, 508.76202111], [470.47798401, 512.17885278],
                                                 [477.40038538, 519.1285721]])

        successor_lane_center_vertices = np.array([[455.62414353, 526.28414086], [455.66775831, 517.47516184],
                                                   [456.83685079, 510.87168633], [459.11570712, 508.19919557],
                                                   [462.31961596, 506.76032058], [465.83105426, 506.83239089],
                                                   [466.33710637, 506.97500951], [471.80641756, 510.85564104],
                                                   [478.72881892, 517.80536036]])

        successor_lane_right_vertices = np.array([[453.74916652, 526.27485753], [453.79278129, 517.4658785],
                                                  [455.17786784, 509.99795836], [457.99083112, 506.69910257],
                                                  [461.9456561,  504.92299127], [466.28008774, 505.01195305],
                                                  [466.90474582, 505.18799792], [473.13485111, 509.5324293],
                                                  [480.05725247, 516.48214862]])
        successor_lane = ConversionLanelet(None, successor_lane_left_vertices, successor_lane_center_vertices,
                                           successor_lane_right_vertices, 100)

        incoming_successor_lane_left_vertices = np.array([[461.40255953, 495.31237109], [461.39716062, 496.40279997],
                                                          [461.7864288,  501.33558294], [462.85415436, 503.93874103],
                                                          [466.04078451, 507.72414271], [477.40038538, 519.1285721]])
        incoming_successor_lane_center_vertices = np.array([[463.27753654, 495.32165442], [463.27213764, 496.4120833],
                                                            [463.60484778, 500.8784425], [464.46984065, 502.98733007],
                                                            [467.36921806, 506.40093097], [478.72881892, 517.80536036]])
        incoming_successor_lane_right_vertices = np.array([[465.15251356, 495.33093775], [465.14711466, 496.42136664],
                                                           [465.42326677, 500.42130205], [466.08552693, 502.0359191],
                                                           [468.69765161, 505.07771923], [480.05725247, 516.48214862]])
        incoming_successor_lane = ConversionLanelet(None, incoming_successor_lane_left_vertices,
                                                    incoming_successor_lane_center_vertices,
                                                    incoming_successor_lane_right_vertices, 101)

        add_lanelets_to_network(conversion_lanelet_network, [lanelet, successor_lane, incoming_successor_lane])
        self.assertTrue(conversion_lanelet_network.check_if_successor_is_intersecting(intersection_map, successor_list))

    def test_get_successor_directions(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)

        center_vertices = np.array([[0, 5.0], [1.0, 5.0],
                                    [2.0, 5.0], [3.0, 5.0],
                                    [4.0, 5.0], [4.5, 5.0]])
        left_vertices = np.empty([5, 2])
        right_vertices = np.empty([5, 2])

        incoming_lane = ConversionLanelet(None, left_vertices, center_vertices, right_vertices, 1)
        incoming_lane.lanelet_id = 6
        incoming_lane.successor = [10]
        left_vertices = np.empty([10, 2])
        right_vertices = np.empty([10, 2])

        center_vertices = np.array([[5.0, 4.9], [5.4, 4.5],
                                    [5.7, 4.0], [5.9, 3.5],
                                    [5.98, 3.0], [6.0, 2.5]])
        successor1 = ConversionLanelet(None, left_vertices, center_vertices, right_vertices, 10)
        add_lanelets_to_network(conversion_lanelet_network, [successor1])
        directions = conversion_lanelet_network.get_successor_directions(incoming_lane)
        # test 1: Single successor with a right curve
        self.assertDictEqual({10: 'right'}, directions)

        # test 2: Two successors, add a left curve to the right curve of test 1
        incoming_lane.successor = [10, 11]
        center_vertices = np.array([[5.0, 5.1], [5.4, 5.5],
                                    [5.7, 6], [5.9, 6.5],
                                    [5.98, 7.0], [6.0, 7.5]])
        successor2 = ConversionLanelet(None, np.empty([6, 2]), center_vertices, np.empty([6, 2]), 11)
        add_lanelets_to_network(conversion_lanelet_network, [successor2])
        directions = conversion_lanelet_network.get_successor_directions(incoming_lane)
        self.assertDictEqual({10: 'right', 11: 'left'}, directions)

        # test 3: Three successors, the two ones of the previous tests plus a straight successor
        incoming_lane.successor = [10, 11, 12]
        center_vertices = np.array([[5.0, 5.0], [5.4, 5.0],
                                    [5.7, 5.0], [5.9, 5.0],
                                    [5.98, 5.0], [6.0, 5.0]])
        successor3 = ConversionLanelet(None, np.empty([6, 2]), center_vertices, np.empty([6, 2]), 12)
        add_lanelets_to_network(conversion_lanelet_network, [successor3])
        directions = conversion_lanelet_network.get_successor_directions(incoming_lane)
        self.assertDictEqual({10: 'right', 11: 'left', 12: 'straight'}, directions)

    def test_add_traffic_signs_to_network(self):
        # construct traffic sign objects: sign1 should be added to lanelet1,
        # sign2 to lanelet2 and sign3 is equidistant to lanelet1 and lanelet2
        # which is added to the first lanelet of the equidistant ones
        sign1 = TrafficSign(0, [], set(), np.array([4.9, -0.1]), virtual=False)
        sign2 = TrafficSign(1, [], set(), np.array([0.1, 4.9]), virtual=False)
        sign3 = TrafficSign(2, [], set(), np.array([4.0, 4.0]), virtual=False)
        traffic_signs = [sign1, sign2, sign3]

        # create conversion lanelet network and corresponding lanelets
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        lanelet1 = ConversionLanelet(None, np.empty([5, 2]), np.array([[0, 0], [1, 0],
                                                                       [2, 0], [3, 0],
                                                                       [4, 0], [5, 0]]), np.empty([5, 2]), 0)
        lanelet2 = ConversionLanelet(None, np.empty([5, 2]), np.array([[0, 0], [0, 1],
                                                                       [0, 2], [0, 3],
                                                                       [0, 4], [0, 5]]), np.empty([5, 2]), 1)

        add_lanelets_to_network(conversion_lanelet_network, [lanelet1, lanelet2])

        conversion_lanelet_network.add_traffic_signs_to_network(traffic_signs)
        lanelet1_true_signs = {0, 1, 2}
        lanelet2_true_signs = set()
        self.assertSetEqual(lanelet1_true_signs, lanelet1.traffic_signs)
        self.assertSetEqual(lanelet2_true_signs, lanelet2.traffic_signs)

    def test_add_stop_lines_to_network(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)

        lanelet_1 = ConversionLanelet(None, np.array([[4, 5], [5, 5]]), np.array([[4, 4], [5, 4]]),
                                      np.array([[4, 3], [5, 3]]), 0)
        stop_line_1 = StopLine(np.array([5, 3]), np.array([5, 5]), None, None, None)

        add_lanelets_to_network(conversion_lanelet_network, [lanelet_1])

        incoming_element = IntersectionIncomingElement(0, {0}, None, None, None, None)

        intersection = Intersection(32, [incoming_element], None)
        conversion_lanelet_network.add_intersection(intersection)

        conversion_lanelet_network.add_stop_lines_to_network([stop_line_1])
        self.assertEqual(stop_line_1, lanelet_1.stop_line)


class TestJointSplitTarget(unittest.TestCase):
    def test_init(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        main_lanelet = init_lanelet_empty_vertices_from_id(None, 0)
        join_split_target = _JoinSplitTarget(conversion_lanelet_network, main_lanelet, True, True,
                                             get_configs().opendrive.precision)
        self.assertEqual(conversion_lanelet_network, join_split_target.lanelet_network)
        self.assertEqual(main_lanelet, join_split_target.main_lanelet)

        self.assertIsNone(join_split_target.change_width)
        self.assertIsNone(join_split_target.linking_side)
        self.assertListEqual([], join_split_target._js_pairs)
        self.assertFalse(join_split_target._single_lanelet_operation)
        self.assertEqual(2, join_split_target._mode)

        join_split_target = _JoinSplitTarget(conversion_lanelet_network, main_lanelet, True, False,
                                             get_configs().opendrive.precision)
        self.assertEqual(1, join_split_target._mode)

        join_split_target = _JoinSplitTarget(conversion_lanelet_network, main_lanelet, False, False,
                                             get_configs().opendrive.precision)
        self.assertEqual(0, join_split_target._mode)

        join_split_target = _JoinSplitTarget(conversion_lanelet_network, main_lanelet, False, True,
                                             get_configs().opendrive.precision)
        self.assertEqual(0, join_split_target._mode)

    def test_split(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        main_lanelet = init_lanelet_empty_vertices_from_id(None, 0)
        join_split_target = _JoinSplitTarget(conversion_lanelet_network, main_lanelet, True, True,
                                             get_configs().opendrive.precision)
        self.assertTrue(join_split_target.split)
        join_split_target = _JoinSplitTarget(conversion_lanelet_network, main_lanelet, False, True,
                                             get_configs().opendrive.precision)
        self.assertFalse(join_split_target.split)

    def test_join(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        main_lanelet = init_lanelet_empty_vertices_from_id(None, 0)
        join_split_target = _JoinSplitTarget(conversion_lanelet_network, main_lanelet, False, True,
                                             get_configs().opendrive.precision)
        self.assertTrue(join_split_target.join)
        join_split_target = _JoinSplitTarget(conversion_lanelet_network, main_lanelet, False, False,
                                             get_configs().opendrive.precision)
        self.assertTrue(join_split_target.join)
        join_split_target = _JoinSplitTarget(conversion_lanelet_network, main_lanelet, True, True,
                                             get_configs().opendrive.precision)
        self.assertTrue(join_split_target.join)
        join_split_target = _JoinSplitTarget(conversion_lanelet_network, main_lanelet, True, False,
                                             get_configs().opendrive.precision)
        self.assertFalse(join_split_target.join)

    def test_split_and_join(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        main_lanelet = init_lanelet_empty_vertices_from_id(None, 0)
        join_split_target = _JoinSplitTarget(conversion_lanelet_network, main_lanelet, True, True,
                                             get_configs().opendrive.precision)
        self.assertTrue(join_split_target.join)
        main_lanelet = init_lanelet_empty_vertices_from_id(None, 0)
        join_split_target = _JoinSplitTarget(conversion_lanelet_network, main_lanelet, False, True,
                                             get_configs().opendrive.precision)
        self.assertFalse(join_split_target.split_and_join)
        main_lanelet = init_lanelet_empty_vertices_from_id(None, 0)
        join_split_target = _JoinSplitTarget(conversion_lanelet_network, main_lanelet, True, False,
                                             get_configs().opendrive.precision)
        self.assertFalse(join_split_target.split_and_join)
        main_lanelet = init_lanelet_empty_vertices_from_id(None, 0)
        join_split_target = _JoinSplitTarget(conversion_lanelet_network, main_lanelet, False, False,
                                             get_configs().opendrive.precision)
        self.assertFalse(join_split_target.split_and_join)

    def test_use_only_single_lanelet(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        main_lanelet = init_lanelet_empty_vertices_from_id(None, 0)
        join_split_target = _JoinSplitTarget(conversion_lanelet_network, main_lanelet, True, True,
                                             get_configs().opendrive.precision)
        join_split_target._single_lanelet_operation = True
        self.assertTrue(join_split_target.use_only_single_lanelet())

        join_split_target = _JoinSplitTarget(conversion_lanelet_network, main_lanelet, True, True,
                                             get_configs().opendrive.precision)
        join_split_target._single_lanelet_operation = False
        self.assertFalse(join_split_target.use_only_single_lanelet())

    def test_find_lanelet_by_id(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        main_lanelet = init_lanelet_empty_vertices_from_id(None, 0)
        lanelet = init_lanelet_empty_vertices_from_id(None, '88.0.3.-1')
        add_lanelets_to_network(conversion_lanelet_network, [lanelet])
        join_split_target = _JoinSplitTarget(conversion_lanelet_network, main_lanelet, True, True,
                                             get_configs().opendrive.precision)
        self.assertEqual(lanelet, join_split_target._find_lanelet_by_id('88.0.3.-1'))

    def test_complete_js_interval_length(self):
        l1 = init_lanelet_empty_vertices_from_id(None, 0)
        l2 = init_lanelet_empty_vertices_from_id(None, 1)
        js_pair1 = _JoinSplitPair(l1, l2, [0, 95], get_configs().opendrive.precision)
        l3 = init_lanelet_empty_vertices_from_id(None, 2)
        l4 = init_lanelet_empty_vertices_from_id(None, 3)
        js_pair2 = _JoinSplitPair(l3, l4, [95, 180], get_configs().opendrive.precision)
        join_split_target = _JoinSplitTarget(None, None, True, True,
                                             get_configs().opendrive.precision)
        join_split_target._js_pairs = [js_pair1, js_pair2]
        self.assertEqual(95+(180-95), join_split_target.complete_js_interval_length())

    def test_adjacent_width(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)

        lanelet = init_lanelet_empty_vertices_from_id(None, '88.0.2.-1')

        plane_group = ParametricLaneGroup()
        plane_group._add_geo_length(100, False)
        reference_plan_view = PlanView()
        reference_plan_view.add_line([0.0, 0.0], 0.5, 100)
        inner_border = Border()
        inner_border.reference = reference_plan_view
        inner_border.width_coefficients.append([3.75, 0, 0, 0])
        inner_border.width_coefficient_offsets.append(0.0)
        outer_border = Border()
        outer_border.reference = reference_plan_view
        outer_border.width_coefficients.append([3.75, 0, 0, 0])
        outer_border.width_coefficient_offsets.append(0.0)
        border_group = ParametricLaneBorderGroup(inner_border, 0.0, outer_border, 0.0)
        parametric_lane = ParametricLane("88.0.3.-1", "driving", border_group, 100, None, None)
        plane_group.parametric_lanes.append(parametric_lane)

        adjacent_lanelet = init_lanelet_empty_vertices_from_id(plane_group, '88.0.3.-1')

        jspair = _JoinSplitPair(lanelet, adjacent_lanelet, [0, 95],
                                get_configs().opendrive.precision)

        join_split_target = _JoinSplitTarget(conversion_lanelet_network, lanelet, True, False,
                                             get_configs().opendrive.precision)

        join_split_target._js_pairs = [jspair]
        join_split_target.adjacent_width(True)

        self.assertEqual(adjacent_lanelet.calc_width_at_start(), join_split_target.adjacent_width(True))
        self.assertEqual(adjacent_lanelet.calc_width_at_end(), join_split_target.adjacent_width(False))

    def test_add_adjacent_predecessor_or_successor(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)

        lanelet = init_lanelet_empty_vertices_from_id(None, '88.0.2.-1')
        adjacent_lanelet = init_lanelet_empty_vertices_from_id(None, '88.0.3.-1')
        adjacent_lanelet_predecessor = init_lanelet_empty_vertices_from_id(None, '82.0.-1.-1')
        adjacent_lanelet.predecessor = ['82.0.-1.-1']
        join_split_target = _JoinSplitTarget(conversion_lanelet_network, lanelet, True, False,
                                             get_configs().opendrive.precision)
        join_split_pair = _JoinSplitPair(lanelet, adjacent_lanelet, [0, 95],
                                         get_configs().opendrive.precision)
        join_split_target._js_pairs.append(join_split_pair)

        add_lanelets_to_network(conversion_lanelet_network, [adjacent_lanelet_predecessor])

        join_split_target.add_adjacent_predecessor_or_successor()

        self.assertListEqual(['82.0.-1.-1'], lanelet.predecessor)
        self.assertListEqual(['88.0.2.-1'], adjacent_lanelet_predecessor.successor)

    def test_move_borders_if_split_or_join(self):
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)

        left_vertices = np.array(
                [[456.37176199, 375.28599181], [456.6199314, 435.28795596], [457.65260563, 495.29380432]])
        center_vertices = np.array(
                [[458.24673901, 375.29527514], [458.49490842, 435.29723929], [459.52758265, 495.30308766]])
        right_vertices = np.array(
                [[460.12171603, 375.30455848], [460.36988543, 435.30652262], [461.40255967, 495.31237099]])

        plane_group = ParametricLaneGroup()
        plane_group._add_geo_length(100, False)
        reference_plan_view = PlanView()
        reference_plan_view.add_line([0.0, 0.0], 0.5, 100)
        inner_border = Border()
        inner_border.reference = reference_plan_view
        inner_border.width_coefficients.append([0, 0, 0, 0])
        inner_border.width_coefficient_offsets.append(0.0)
        outer_border = Border()
        outer_border.reference = reference_plan_view
        outer_border.width_coefficients.append([3.75, 0, 0, 0])
        outer_border.width_coefficient_offsets.append(0.0)
        border_group = ParametricLaneBorderGroup(inner_border, 0.0, outer_border, 0.0)
        parametric_lane = ParametricLane("88.0.3.-1", "driving", border_group, 100, None, None)
        plane_group.parametric_lanes.append(parametric_lane)

        lanelet = init_lanelet_empty_vertices_from_id(plane_group, '88.0.2.-1')
        adjacent_lanelet = ConversionLanelet(plane_group, left_vertices, center_vertices, right_vertices, '88.0.3.-1')

        jspair = _JoinSplitPair(lanelet, adjacent_lanelet, [0, 95],
                                get_configs().opendrive.precision)
        # test with split
        join_split_target = _JoinSplitTarget(conversion_lanelet_network, lanelet, True, False,
                                             get_configs().opendrive.precision)

        join_split_target._js_pairs = [jspair]
        join_split_target.change_width = 3.75
        join_split_target._move_borders_if_split_or_join()

        true_new_lanelet = lanelet.parametric_lane_group.to_lanelet_with_mirroring(None, [3.75, 3.75],
                                                                                   [0, 95], adjacent_lanelet)
        self.assertListEqual(true_new_lanelet.left_vertices.tolist(), lanelet.left_vertices.tolist())
        self.assertListEqual(true_new_lanelet.center_vertices.tolist(), lanelet.center_vertices.tolist())
        self.assertListEqual(true_new_lanelet.right_vertices.tolist(), lanelet.right_vertices.tolist())
        # test with join
        join_split_target = _JoinSplitTarget(conversion_lanelet_network, lanelet, False, True,
                                             get_configs().opendrive.precision)

        join_split_target._js_pairs = [jspair]
        join_split_target.change_width = 3.75
        join_split_target._move_borders_if_split_or_join()

        true_new_lanelet = lanelet.parametric_lane_group.to_lanelet_with_mirroring(None, [3.75, 3.75],
                                                                                   [0, 95], adjacent_lanelet)
        self.assertListEqual(true_new_lanelet.left_vertices.tolist(), lanelet.left_vertices.tolist())
        self.assertListEqual(true_new_lanelet.center_vertices.tolist(), lanelet.center_vertices.tolist())
        self.assertListEqual(true_new_lanelet.right_vertices.tolist(), lanelet.right_vertices.tolist())


class TestJoinSplitPair(unittest.TestCase):

    def test_init(self):
        lanelet = init_lanelet_empty_vertices_from_id(None, '100.0.0.0')
        adjacent_lanelet = init_lanelet_empty_vertices_from_id(None, '100.0.1.0')
        change_interval = [0, 95]
        join_split_pair = _JoinSplitPair(lanelet, adjacent_lanelet, change_interval,
                                         get_configs().opendrive.precision)
        self.assertEqual(lanelet, join_split_pair.lanelet)
        self.assertEqual(adjacent_lanelet, join_split_pair.adjacent_lanelet)
        self.assertListEqual(change_interval, join_split_pair.change_interval)

    def test_move_border(self):

        plane_group = ParametricLaneGroup()

        reference_view = PlanView()
        reference_view.add_line(0, 0.5, 120)

        inner_border = Border()
        inner_border.reference = reference_view
        inner_border.width_coefficients.append([0.0, 0.0, 0.0, 0.0])
        inner_border.width_coefficient_offsets.append(0.0)
        outer_border = Border()
        outer_border.reference = reference_view
        outer_border.width_coefficients.append([3.75, 0, 0, 0])
        outer_border.width_coefficient_offsets.append(0.0)
        border_group = ParametricLaneBorderGroup(inner_border, 52, outer_border, 52)
        plane = ParametricLane("88.0.2.2", "driving", border_group, 68, None, "left")
        plane_group._geo_lengths = np.insert(plane_group._geo_lengths, 1, 120)
        plane_group.parametric_lanes.append(plane)

        lanelet = init_lanelet_empty_vertices_from_id(plane_group, '88.0.2.-1')
        adjacent_lanelet = init_lanelet_empty_vertices_from_id(plane_group, '88.0.3.-1')
        js_pair = _JoinSplitPair(lanelet, adjacent_lanelet, [0, 95],
                                 get_configs().opendrive.precision)

        linking_side = "left"
        js_pair.mirror_interval = [0, 95]
        width = np.array([3.75, 3.75])

        new_lanelet = js_pair.move_border(width, linking_side)

        width[:] = [-1 * x for x in width]
        true_new_lanelet = lanelet.parametric_lane_group.to_lanelet_with_mirroring("left", js_pair.mirror_interval,
                                                                                   width, adjacent_lanelet)
        true_new_lanelet.left_vertices = lanelet.left_vertices
        true_new_lanelet.center_vertices = lanelet.center_vertices
        true_new_lanelet.right_vertices = lanelet.right_vertices

        self.assertListEqual(true_new_lanelet.left_vertices.tolist(), new_lanelet.left_vertices.tolist())
        self.assertListEqual(true_new_lanelet.center_vertices.tolist(), new_lanelet.center_vertices.tolist())
        self.assertListEqual(true_new_lanelet.right_vertices.tolist(), new_lanelet.right_vertices.tolist())
