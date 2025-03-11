import logging
from typing import Set, Tuple

import numpy as np
from commonroad.common.common_lanelet import StopLine
from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.scenario.scenario import ScenarioID
from commonroad.scenario.traffic_light import TrafficLight
from commonroad.scenario.traffic_sign import TrafficSign
from commonroad_clcs.util import compute_orientation_from_polyline
from shapely.geometry import LineString, Point
from shapely.ops import nearest_points

from crdesigner.verification_repairing.repairing.repairing import ElementRepairing
from crdesigner.verification_repairing.repairing.tools.geometry_tools import (
    average_vertices,
    check_intersected_lines,
    check_line_intersection_efficient,
    fill_number_of_vertices,
    insert_vertices,
)


class LaneletRepairing(ElementRepairing):
    """
    The class includes all repairing methods for each supported formula concerning the lanelet element.
    """

    def __init__(self, network: LaneletNetwork, scenario_id: ScenarioID = ScenarioID()):
        """
        Constructor.

        :param network: Lanelet network.
        :param scenario_id: ScenarioID.
        """
        super().__init__(network, scenario_id)
        self._connections = {}
        self._composed_lanelets = {}

    def repair_unique_id(self, location: Tuple[int]):
        """
        Repairs unique_id.

        :param location: Location of invalid state.
        """
        (lanelet_id,) = location

        lanelet_ids = [lanelet.lanelet_id for lanelet in self._network.lanelets]

        new_lanelet_id = max(lanelet_ids) + 1

        lanelet = self._network.find_lanelet_by_id(lanelet_id)
        lanelet.lanelet_id = new_lanelet_id

    def repair_same_vertices_size(self, location: Tuple[int]):
        """
        Repairs same_vertices_size.

        :param location: Location of invalid state.
        """
        (lanelet_id,) = location

        lanelet = self._network.find_lanelet_by_id(lanelet_id)

        left_vertices = lanelet.left_vertices
        right_vertices = lanelet.right_vertices

        if len(left_vertices) > len(right_vertices):
            lanelet.right_vertices = insert_vertices(left_vertices, right_vertices)
        elif len(left_vertices) < len(right_vertices):
            lanelet.left_vertices = insert_vertices(right_vertices, left_vertices)

    def repair_vertices_more_than_one(self, location: Tuple[int]):
        """
        Repairs vertices_more_than_one.

        :param location: Location of invalid state.
        """
        (lanelet_id,) = location

        self._network.remove_lanelet(lanelet_id)

    def repair_existence_left_adj(self, location: Tuple[int]):
        """
        Repairs existence_left_adj.

        :param location: Location of invalid state.
        """
        self._repair_wrong_adjacency_reference(location, is_left=True)

    def repair_existence_right_adj(self, location: Tuple[int]):
        """
        Repairs existence_right_adj.

        :param location: Location of invalid state.
        """
        self._repair_wrong_adjacency_reference(location, is_left=False)

    def repair_existence_predecessor(self, location: Tuple[int, int]):
        """
        Repairs existence_predecessor.

        :param location: Location of invalid state.
        """
        self._repair_wrong_pred_suc_reference(location, is_pred=True)

    def repair_existence_successor(self, location: Tuple[int, int]):
        """
        Repairs existence_successor.

        :param location: Location of invalid state.
        """
        self._repair_wrong_pred_suc_reference(location, is_pred=False)

    def repair_connections_predecessor(self, location: Tuple[int, int]):
        """
        Repairs connections_predecessor.

        :param location: Location of invalid state.
        """
        self._repair_connection_predecessor_successor(location, is_pred=True)

    def repair_connections_successor(self, location: Tuple[int, int]):
        """
        Repairs connections_successor.

        :param location: Location of invalid state.
        """
        self._repair_connection_predecessor_successor(location, is_pred=False)

    def repair_polylines_left_same_dir_parallel_adj(self, location: Tuple[int, int]):
        """
        Repairs polylines_left_same_dir_parallel_adj.

        :param location: Location of invalid state.
        """
        self._repair_normal_adjacency(location, is_left=True, is_same=True)

    def repair_polylines_left_opposite_dir_parallel_adj(self, location: Tuple[int, int]):
        """
        Repairs polylines_left_opposite_dir_parallel_adj.

        :param location: Location of invalid state.
        """
        self._repair_normal_adjacency(location, is_left=True, is_same=False)

    def repair_polylines_right_same_dir_parallel_adj(self, location: Tuple[int, int]):
        """
        Repairs polylines_right_same_dir_parallel_adj.

        :param location: Location of invalid state.
        """
        self._repair_normal_adjacency(location, is_left=False, is_same=True)

    def repair_polylines_right_opposite_dir_parallel_adj(self, location: Tuple[int, int]):
        """
        Repairs polylines_right_opposite_dir_parallel_adj.

        :param location: Location of invalid state.
        """
        self._repair_normal_adjacency(location, is_left=False, is_same=False)

    def repair_connections_left_merging_adj(self, location: Tuple[int, int]):
        """
        Repairs connections_left_merging_adj.

        :param location: Location of invalid state.
        """
        self._repair_connections_adjacency(location, is_left_adj=True, is_merging_adj=True)

    def repair_connections_right_merging_adj(self, location: Tuple[int, int]):
        """
        Repairs connections_right_merging_adj.

        :param location: Location of invalid state.
        """
        self._repair_connections_adjacency(location, is_left_adj=False, is_merging_adj=True)

    def repair_connections_left_forking_adj(self, location: Tuple[int, int]):
        """
        Repairs connections_left_forking_adj.

        :param location: Location of invalid state.
        """
        self._repair_connections_adjacency(location, is_left_adj=True, is_merging_adj=False)

    def repair_connections_right_forking_adj(self, location: Tuple[int, int]):
        """
        Repairs connections_right_forking_adj.

        :param location: Location of invalid state.
        """
        self._repair_connections_adjacency(location, is_left_adj=False, is_merging_adj=False)

    def repair_potential_successor(self, location: Tuple[int, int]):
        """
        Repairs potential_successor.

        :param location: Location of invalid state.
        """
        self._repair_possible_predecessor_successor(location, is_pred=False)

    def repair_potential_predecessor(self, location: Tuple[int, int]):
        """
        Repairs potential_predecessor.

        :param location: Location of invalid state.
        """
        self._repair_possible_predecessor_successor(location, is_pred=True)

    def repair_potential_left_same_dir_parallel_adj(self, location: Tuple[int, int]):
        """
        Repairs potential_left_same_dir_parallel_adj.

        :param location: Location of invalid state.
        """
        self._repair_possible_adjacency(location, is_left=True, is_same=True)

    def repair_potential_left_opposite_dir_parallel_adj(self, location: Tuple[int, int]):
        """
        Repairs potential_left_opposite_dir_parallel_adj.

        :param location: Location of invalid state.
        """
        self._repair_possible_adjacency(location, is_left=True, is_same=False)

    def repair_potential_right_same_dir_parallel_adj(self, location: Tuple[int, int]):
        """
        Repairs potential_right_same_dir_parallel_adj.

        :param location: Location of invalid state.
        """
        self._repair_possible_adjacency(location, is_left=False, is_same=True)

    def repair_potential_right_opposite_dir_parallel_adj(self, location: Tuple[int, int]):
        """
        Repairs potential_right_opposite_dir_parallel_adj.

        :param location: Location of invalid state.
        """
        self._repair_possible_adjacency(location, is_left=False, is_same=False)

    def repair_potential_left_merging_adj(self, location: Tuple[int, int]):
        """
        Repairs potential_left_merging_adj.

        :param location: Location of invalid state.
        """
        self._repair_possible_adjacency(location, is_left=True, is_same=True)

    def repair_potential_right_merging_adj(self, location: Tuple[int, int]):
        """
        Repairs potential_right_merging_adj.

        :param location: Location of invalid state.
        """
        self._repair_possible_adjacency(location, is_left=False, is_same=True)

    def repair_potential_left_forking_adj(self, location: Tuple[int, int]):
        """
        Repairs potential_left_forking_adj.

        :param location: Location of invalid state.
        """
        self._repair_possible_adjacency(location, is_left=True, is_same=True)

    def repair_potential_right_forking_adj(self, location: Tuple[int, int]):
        """
        Repairs potential_right_forking_adj.

        :param location: Location of invalid state.
        """
        self._repair_possible_adjacency(location, is_left=False, is_same=True)

    def repair_non_predecessor_as_successor(self, location: Tuple[int, int]):
        """
        Repairs non_predecessor_as_successor.

        :param location: Location of invalid state.
        """
        lanelet_id, predecessor_id = location

        lanelet = self._network.find_lanelet_by_id(lanelet_id)

        if predecessor_id in lanelet.successor:
            lanelet.successor.remove(predecessor_id)

        if predecessor_id not in lanelet.predecessor:
            lanelet.predecessor.append(predecessor_id)

    def repair_non_successor_as_predecessor(self, location: Tuple[int, int]):
        """
        Repairs non_successor_as_predecessor.

        :param location: Location of invalid state.
        """
        lanelet_id, successor_id = location

        lanelet = self._network.find_lanelet_by_id(lanelet_id)

        if successor_id in lanelet.predecessor:
            lanelet.predecessor.remove(successor_id)

        if successor_id not in lanelet.successor:
            lanelet.successor.append(successor_id)

    def repair_polylines_intersection(self, location: Tuple[int]):
        """
        Repairs polylines_intersection. For the crossing intermediate lines the respective points
        are changed successively.

        :param location: Location of invalid state.
        """
        (lanelet_id,) = location

        lanelet = self._network.find_lanelet_by_id(lanelet_id)

        right_vertices = lanelet.right_vertices
        left_vertices = lanelet.left_vertices

        if np.array_equal(right_vertices[-1], left_vertices[-1]):
            right_vertices[-1] = (
                right_vertices[-1] + (right_vertices[-2] - left_vertices[-2]) * 0.01
            )
            left_vertices[-1] = left_vertices[-1] + (left_vertices[-2] - right_vertices[-2]) * 0.01
        if np.array_equal(right_vertices[0], left_vertices[0]):
            right_vertices[0] = right_vertices[0] + (right_vertices[1] - left_vertices[1]) * 0.01
            left_vertices[0] = left_vertices[0] + (left_vertices[1] - right_vertices[1]) * 0.01

        vertices_size = len(left_vertices)
        for vert_right_i in range(0, vertices_size - 1):
            for vert_left_i in range(0, vertices_size - 1):
                right_start_point = right_vertices[vert_right_i]
                right_end_point = right_vertices[vert_right_i + 1]
                left_start_point = left_vertices[vert_left_i]
                left_end_point = left_vertices[vert_left_i + 1]

                if not check_line_intersection_efficient(
                    [right_start_point, right_end_point], [left_start_point, left_end_point]
                ):
                    continue

                right_end_point_copy = right_end_point.copy()
                right_vertices[vert_right_i + 1] = left_end_point
                left_vertices[vert_left_i + 1] = right_end_point_copy

    def repair_left_self_intersection(self, location: Tuple[int]):
        """
        Repairs left_self_intersection.

        :param location: Location of invalid state.
        """
        self._repair_polyline_self_intersection(location, is_left=True)

    def repair_right_self_intersection(self, location: Tuple[int]):
        """
        Repairs right_self_intersection.

        :param location: Location of invalid state.
        """
        self._repair_polyline_self_intersection(location, is_left=False)

    def repair_lanelet_types_combination(self, location: Tuple[int, int, int]):
        """
        Repairs lanelet_types_combination.

        :param location: Location of invalid state.
        """
        lanelet_id, lanelet_type_0, lanelet_type_1 = location

        lanelet = self._network.find_lanelet_by_id(lanelet_id)

        l_types = lanelet.lanelet_type
        for l_type in l_types:
            if lanelet_type_0 == hash(l_type.value):
                lanelet_type_0 = l_type
            if lanelet_type_1 == hash(l_type.value):
                lanelet_type_1 = l_type

        if lanelet_type_0 in l_types and lanelet_type_1 in l_types:
            lanelet.lanelet_type.remove(lanelet_type_1)

    def repair_non_followed_composable_lanelets(self, location: Tuple[int, int]):
        """
        Repairs non_followed_composable_lanelets.

        :param location: Location of invalid state.
        """
        lanelet_id, successor_id = location

        while True:
            pre_lanelet_id = lanelet_id
            pre_successor_id = successor_id
            lanelet_id = self._composed_lanelets.get(lanelet_id, lanelet_id)
            successor_id = self._composed_lanelets.get(successor_id, successor_id)

            if pre_lanelet_id == lanelet_id and pre_successor_id == successor_id:
                break
            elif lanelet_id == successor_id:
                return

        valid_dir = True
        while True:
            lanelet = self._network.find_lanelet_by_id(lanelet_id)
            successor = self._network.find_lanelet_by_id(successor_id)

            if lanelet is None or successor is None:
                return

            new_lanelet_id = lanelet.adj_right if valid_dir else lanelet.adj_left
            new_successor_id = successor.adj_right if valid_dir else successor.adj_left

            valid_dir = lanelet.adj_right_same_direction

            if new_lanelet_id is None or new_successor_id is None:
                break

            lanelet_id = new_lanelet_id
            successor_id = new_successor_id

        pre_valid_dir = True
        valid_dir = True
        pre_merged_lanelet_id = None
        while lanelet_id is not None and successor_id is not None:
            lanelet = self._network.find_lanelet_by_id(lanelet_id)
            successor = self._network.find_lanelet_by_id(successor_id)

            merged_lanelet = lanelet.merge_lanelets(lanelet, successor)
            merged_lanelet_id = merged_lanelet.lanelet_id

            merged_lanelet.lanelet_type = lanelet.lanelet_type

            successor_successor = successor.successor if valid_dir else successor.predecessor
            for suc_id in successor_successor:
                suc = self._network.find_lanelet_by_id(suc_id)
                if valid_dir:
                    suc.predecessor.append(merged_lanelet_id)
                else:
                    suc.successor.append(merged_lanelet_id)

            lanelet_predecessor = lanelet.predecessor if valid_dir else lanelet.successor
            for pred_id in lanelet_predecessor:
                pred = self._network.find_lanelet_by_id(pred_id)
                if valid_dir:
                    pred.successor.append(merged_lanelet_id)
                else:
                    pred.predecessor.append(merged_lanelet_id)

            if pre_merged_lanelet_id is not None:
                pre_merged_lanelet = self._network.find_lanelet_by_id(pre_merged_lanelet_id)
                if pre_valid_dir:
                    if valid_dir:
                        merged_lanelet.adj_right = pre_merged_lanelet_id
                        merged_lanelet.adj_right_same_direction = True
                        pre_merged_lanelet.adj_left = merged_lanelet_id
                        pre_merged_lanelet.adj_left_same_direction = True
                    else:
                        merged_lanelet.adj_left = pre_merged_lanelet_id
                        merged_lanelet.adj_left_same_direction = False
                        pre_merged_lanelet.adj_right = merged_lanelet_id
                        pre_merged_lanelet.adj_right_same_direction = False
                else:
                    if valid_dir:
                        merged_lanelet.adj_right = pre_merged_lanelet_id
                        merged_lanelet.adj_right_same_direction = False
                        pre_merged_lanelet.adj_left = merged_lanelet_id
                        pre_merged_lanelet.adj_left_same_direction = False
                    else:
                        merged_lanelet.adj_left = pre_merged_lanelet_id
                        merged_lanelet.adj_left_same_direction = True
                        pre_merged_lanelet.adj_right = merged_lanelet_id
                        pre_merged_lanelet.adj_right_same_direction = True

            for intersection in self._network.intersections:
                for incoming in intersection.incomings:
                    incoming_lanelets = incoming.incoming_lanelets
                    if lanelet_id in incoming_lanelets or successor_id in incoming_lanelets:
                        incoming_lanelets.add(merged_lanelet_id)

            new_lanelet_id = lanelet.adj_left if valid_dir else lanelet.adj_right
            new_successor_id = successor.adj_left if valid_dir else successor.adj_right

            if valid_dir:
                new_valid_dir = lanelet.adj_left_same_direction
            else:
                new_valid_dir = not lanelet.adj_right_same_direction

            self._network.add_lanelet(merged_lanelet)
            self._network.remove_lanelet(lanelet_id)
            self._network.remove_lanelet(successor_id)

            self._composed_lanelets.update({lanelet_id: merged_lanelet_id})
            self._composed_lanelets.update({successor_id: merged_lanelet_id})

            lanelet_id = new_lanelet_id
            successor_id = new_successor_id

            pre_valid_dir = valid_dir
            valid_dir = new_valid_dir

            pre_merged_lanelet_id = merged_lanelet_id

    def repair_referenced_intersecting_lanelets(self, location: Tuple[int, int]):
        """
        Repairs referenced_intersecting_lanelets.

        :param location: Location of invalid state.
        """
        # lanelet_id_0, lanelet_id_1 = location

        # lanelet_0 = self._network.find_lanelet_by_id(lanelet_id_0)
        # lanelet_1 = self._network.find_lanelet_by_id(lanelet_id_1)

        #  shapely_polygon_1 = lanelet_1.polygon.shapely_object.difference(lanelet_0.polygon.shapely_object)
        pass  # TODO: Implement

    def repair_existence_traffic_signs(self, location: Tuple[int, int]):
        """
        Repairs existence_traffic_signs.

        :param location: Location of invalid state.
        """
        lanelet_id, traffic_sign_id = location

        lanelet = self._network.find_lanelet_by_id(lanelet_id)
        lanelet.traffic_signs.remove(traffic_sign_id)

    def repair_existence_traffic_lights(self, location: Tuple[int, int]):
        """
        Repairs existence_traffic_lights.

        :param location: Location of invalid state.
        """
        lanelet_id, traffic_light_id = location

        lanelet = self._network.find_lanelet_by_id(lanelet_id)
        lanelet.traffic_lights.remove(traffic_light_id)

    def repair_existence_stop_line_traffic_signs(self, location: Tuple[int, int]):
        """
        Repairs existence_stop_line_traffic_signs.

        :param location: Location of invalid state.
        """
        lanelet_id, traffic_sign_id = location

        lanelet = self._network.find_lanelet_by_id(lanelet_id)
        lanelet.stop_line.traffic_sign_ref.remove(traffic_sign_id)

    def repair_existence_stop_line_traffic_lights(self, location: Tuple[int, int]):
        """
        Repairs existence_stop_line_traffic_lights.

        :param location: Location of invalid state.
        """
        lanelet_id, traffic_light_id = location

        lanelet = self._network.find_lanelet_by_id(lanelet_id)
        lanelet.stop_line.traffic_light_ref.remove(traffic_light_id)

    def repair_included_stop_line_traffic_signs(self, location: Tuple[int, int]):
        """
        Repairs included_stop_line_traffic_signs.

        :param location: Location of invalid state.
        """
        lanelet_id, traffic_sign_id = location

        lanelet = self._network.find_lanelet_by_id(lanelet_id)
        if self._network.find_traffic_sign_by_id(
            traffic_sign_id
        ) is not None and self._regulatory_element_close_to_stop_line(
            self._network.find_traffic_sign_by_id(traffic_sign_id).position, lanelet.stop_line
        ):
            lanelet.traffic_signs.add(traffic_sign_id)
        else:
            relevant_traffic_signs = self._find_relevant_stop_line_signs(lanelet.stop_line)
            relevant_traffic_lights = self._find_relevant_stop_line_lights(lanelet.stop_line)
            lanelet.stop_line.traffic_sign_ref = relevant_traffic_signs
            lanelet.stop_line.traffic_light_ref = relevant_traffic_lights

    def repair_included_stop_line_traffic_lights(self, location: Tuple[int, int]):
        """
        Repairs included_stop_line_traffic_lights.

        :param location: Location of invalid state.
        """
        lanelet_id, traffic_light_id = location

        lanelet = self._network.find_lanelet_by_id(lanelet_id)
        lanelet.traffic_lights.add(traffic_light_id)

    def repair_zero_or_two_points_stop_line(self, location: Tuple[int]):
        """
        Repairs zero_or_two_points_stop_line.

        :param location: Location of invalid state.
        """
        (lanelet_id,) = location

        lanelet = self._network.find_lanelet_by_id(lanelet_id)
        lanelet.stop_line.start = None
        lanelet.stop_line.end = None

    def repair_stop_line_points_on_polylines(self, location: Tuple[int]):
        """
        Repairs stop_line_points_on_polylines.

        :param location: Location of invalid state.
        """
        (lanelet_id,) = location

        lanelet = self._network.find_lanelet_by_id(lanelet_id)
        stop_line = lanelet.stop_line

        left_line = LineString(lanelet.left_vertices)
        left_point = Point(stop_line.start)
        p1, _ = nearest_points(left_line, left_point)
        stop_line.start = np.array([p1.x, p1.y])

        right_line = LineString(lanelet.right_vertices)
        right_point = Point(stop_line.end)
        p2, _ = nearest_points(right_line, right_point)
        stop_line.end = np.array([p2.x, p2.y])

    def repair_stop_line_references(self, location: Tuple[int]):
        """
        Repairs invalid references to traffic signs/lights by stop lines.

        :param location: Lanelet of invalid stop line.
        """
        (lanelet_id,) = location
        lanelet = self._network.find_lanelet_by_id(lanelet_id)

        relevant_traffic_signs = self._find_relevant_stop_line_signs(lanelet.stop_line)
        relevant_traffic_lights = self._find_relevant_stop_line_lights(lanelet.stop_line)
        lanelet.stop_line.traffic_sign_ref = relevant_traffic_signs
        lanelet.stop_line.traffic_light_ref = relevant_traffic_lights

    def repair_left_right_boundary_assignment(self, location: Tuple[int]):
        """
        Repairs lanelet where left and right boundary are swapped.

        :param location: ID of invalid lanelet.
        """
        lanelet = self._network.find_lanelet_by_id(location[0])
        lanelet.right_vertices, lanelet.left_vertices = (
            lanelet.left_vertices,
            lanelet.right_vertices,
        )
        lanelet.center_vertices = (lanelet.left_vertices + lanelet.right_vertices) / 2

    def repair_conflicting_lanelet_directions(self, location: Tuple[int, int]):
        """
        Repairs lanelets where ends point to each other.

        :param location: IDs of the two invalid lanelets.
        """
        logging.error(
            "repair_conflicting_lanelet_directions: "
            "Cannot be repaired automatically. Please contact developers."
        )

    def _find_relevant_stop_line_signs(self, stop_line: StopLine) -> Set[TrafficSign]:
        """
        Extracts traffic signs which could be corresponding traffic sign for stop line.

        :param stop_line: Stop line of interest.
        """
        return {
            sign.traffic_sign_id
            for sign in self._network.traffic_signs
            if self._regulatory_element_close_to_stop_line(sign.position, stop_line)
        }

    def _find_relevant_stop_line_lights(self, stop_line: StopLine) -> Set[TrafficLight]:
        """
        Extracts traffic lights which could be corresponding traffic light for stop line.

        :param stop_line: Stop line of interest.
        """
        return {
            light.traffic_light_id
            for light in self._network.traffic_lights
            if self._regulatory_element_close_to_stop_line(light.position, stop_line)
        }

    def _regulatory_element_close_to_stop_line(
        self, position: np.ndarray, stop_line: StopLine
    ) -> bool:
        """
        Evaluates whether stop line is close to a given position.

        :param position: Position of regulator element, e.g., traffic sign or light
        :param stop_line: Stop line
        :return: Boolean indicating whether position is close to stop line
        """
        return (
            min(
                np.linalg.norm(stop_line.start - position), np.linalg.norm(stop_line.end - position)
            )
            < 10
        )

    def _optimal_vertice(
        self,
        fst_lanelet_id: int,
        snd_lanelet_id: int,
        fst_vertices: np.ndarray,
        snd_vertices: np.ndarray,
        is_fst_start: bool,
        is_snd_start: bool,
    ):
        """
        For two points from the two given polylines of two different lanelets the average are computed and
        the index of the points in their polyline are overwritten by the averaged optimal point. In the exact mode
        the two points are stored as bundle so that if one of the points in the subsequent repairing process is
        changed all partners in the bundle are equalized.

        :param fst_lanelet_id: ID of first lanelet.
        :param snd_lanelet_id: ID of second lanelet.
        :param fst_vertices: Vertices of first lanelet.
        :param snd_vertices: Vertices of second lanelet
        :param is_fst_start: Boolean indicates whether the starting or ending point of vertices of first lanelet should
        be considered.
        :param is_snd_start: Boolean indicates whether the starting or ending point of vertices of second lanelet shoud
        be considered.
        """
        left_i = 0 if is_fst_start else fst_vertices.shape[0] - 1
        right_i = 0 if is_snd_start else snd_vertices.shape[0] - 1

        left_vertex = fst_vertices[left_i]
        right_vertex = snd_vertices[right_i]

        opt_vertex = [
            (left_vertex[0] + right_vertex[0]) / 2,
            (left_vertex[1] + right_vertex[1]) / 2,
        ]

        # check if the vertex is 3d
        if len(left_vertex) == 3:
            opt_vertex = [
                (left_vertex[0] + right_vertex[0]) / 2,
                (left_vertex[1] + right_vertex[1]) / 2,
                (left_vertex[2] + right_vertex[2]) / 2,
            ]

        left_vertice_tuple = (str(left_vertex[0]), str(left_vertex[1]))
        right_vertice_tuple = (str(right_vertex[0]), str(right_vertex[1]))
        left_connections: list = self._connections.get(left_vertice_tuple)
        right_connections: list = self._connections.get(right_vertice_tuple)

        if left_connections is None:
            left_connections = []
        else:
            del self._connections[left_vertice_tuple]
        if right_connections is None:
            right_connections = []
        else:
            if str(left_vertex) != str(right_vertex):
                del self._connections[right_vertice_tuple]

        connections = left_connections + right_connections

        for _, vertices, is_vert_start in connections:
            vert_size = vertices.shape[0]
            vert_i = 0 if is_vert_start else vert_size - 1
            vertices[vert_i] = opt_vertex

        connections = connections + [
            (fst_lanelet_id, fst_vertices, is_fst_start),
            (snd_lanelet_id, snd_vertices, is_snd_start),
        ]

        optimal_vertice_tuple = (str(opt_vertex[0]), str(opt_vertex[1]))
        self._connections.update({optimal_vertice_tuple: connections})

        fst_vertices[left_i] = opt_vertex
        snd_vertices[right_i] = opt_vertex

    def _repair_wrong_pred_suc_reference(self, location: Tuple[int, int], is_pred: bool):
        """
        Repairs existence_predecessor and existence_successor. The reference to predecessor or
        successor from lanelet is removed.

        :param location: Location of invalid state.
        :param is_pred: Boolean indicates whether the predecessor or successor of lanelet should be considered.
        """
        lanelet_id, pred_suc_ref = location

        lanelet = self._network.find_lanelet_by_id(lanelet_id)

        if is_pred:
            lanelet.predecessor.remove(pred_suc_ref)
        else:
            lanelet.successor.remove(pred_suc_ref)

    def _repair_wrong_adjacency_reference(self, location: Tuple[int], is_left: bool):
        """
        Repairs existence_left_adj and existence_right_adj. The reference to adjacency from
        lanelet is removed.

        :param location: Location of invalid state.
        :param is_left: Boolean indicates whether the wrongly referenced left or right adjacency should be considered.
        """
        (lanelet_id,) = location

        lanelet = self._network.find_lanelet_by_id(lanelet_id)

        if is_left:
            lanelet.adj_left = None
        else:
            lanelet.adj_right = None

    def _repair_connection_predecessor_successor(self, location: Tuple[int, int], is_pred: bool):
        """
        Repairs connections_predecessor and connections_successor. The connection points are averaged
        and equalized.

        :param location: Location of invalid state.
        :param is_pred: Boolean indicates whether the invalid left or right connection should be considered.
        """
        lanelet_id, pred_suc_id = location

        lanelet = self._network.find_lanelet_by_id(lanelet_id)
        pred_suc = self._network.find_lanelet_by_id(pred_suc_id)

        # in case of an existing wrong predecessor/successor assignment remove reference
        if is_pred and (
            min(
                np.linalg.norm(lanelet.left_vertices[0] - pred_suc.left_vertices[-1]),
                np.linalg.norm(lanelet.right_vertices[0] - pred_suc.right_vertices[-1]),
            )
            > 2
            or (
                np.linalg.norm(lanelet.left_vertices[0] - pred_suc.left_vertices[-1])
                + np.linalg.norm(lanelet.right_vertices[0] - pred_suc.right_vertices[-1])
            )
            / 2
            > 4
        ):
            lanelet.predecessor.remove(pred_suc_id)
            return
        if not is_pred and (
            min(
                np.linalg.norm(lanelet.left_vertices[-1] - pred_suc.left_vertices[0]),
                np.linalg.norm(lanelet.right_vertices[-1] - pred_suc.right_vertices[0]),
            )
            > 2
            or (
                np.linalg.norm(lanelet.left_vertices[-1] - pred_suc.left_vertices[0])
                + np.linalg.norm(lanelet.right_vertices[-1] - pred_suc.right_vertices[0])
            )
            > 4
        ):
            lanelet.successor.remove(pred_suc_id)
            return

        lanelet_vertices = lanelet.left_vertices
        pred_suc_vertices = pred_suc.left_vertices

        self._optimal_vertice(
            lanelet_id, pred_suc_id, lanelet_vertices, pred_suc_vertices, is_pred, not is_pred
        )

        lanelet_vertices = lanelet.right_vertices
        pred_suc_vertices = pred_suc.right_vertices

        self._optimal_vertice(
            lanelet_id, pred_suc_id, lanelet_vertices, pred_suc_vertices, is_pred, not is_pred
        )

    def _repair_possible_predecessor_successor(self, location: Tuple[int, int], is_pred: bool):
        """
        Repairs potential_predecessor and potential_successor. The detected potential lanelets predecessor and
        successor are referenced.

        :param location: Location of invalid state.
        :param is_pred: Boolean indicates whether the unreferenced predecessor or successor should be considered.
        """
        lanelet_id, possible_pred_suc_id = location

        lanelet = self._network.find_lanelet_by_id(lanelet_id)
        if is_pred:
            lanelet.predecessor.append(possible_pred_suc_id)
        else:
            lanelet.successor.append(possible_pred_suc_id)

    def _repair_polyline_self_intersection(self, location: Tuple[int], is_left: bool):
        """
        Repairs left_self_intersection and right_self_intersection. The intersected intermediate lines are
        successively removed. For the intersecting parts a new intermediate line is placed.

        :param location: Location of invalid state.
        :param is_left: Boolean indicates whether the left or right polyline should be considered.
        """
        (lanelet_id,) = location

        lanelet = self._network.find_lanelet_by_id(lanelet_id)

        intersected_vertices = lanelet.left_vertices if is_left else lanelet.right_vertices

        origin_vertices_size = len(intersected_vertices)

        for vert_i in range(0, origin_vertices_size - 1):
            for vert_j in range(vert_i, origin_vertices_size - 1):
                vertices_size = len(intersected_vertices)
                if vert_i == vert_j:
                    continue
                if vertices_size - 2 < vert_i or vertices_size - 2 < vert_j:
                    break

                init_end_vertex = intersected_vertices[vert_i + 1]

                init_line = np.array([intersected_vertices[vert_i], init_end_vertex])
                successive_line = np.array(
                    [intersected_vertices[vert_j], intersected_vertices[vert_j + 1]]
                )

                excluded_points = []
                if vert_i + 1 == vert_j:
                    excluded_points = [[init_end_vertex[0], init_end_vertex[1]]]
                if not check_intersected_lines(init_line, successive_line, excluded_points):
                    continue

                new_vertices = []
                for new_vert_i in range(0, vertices_size):
                    if vert_i < new_vert_i < vert_j + 1:
                        continue
                    new_vertices.append(intersected_vertices[new_vert_i])

                intersected_vertices = np.array(new_vertices)

        non_intersecting_vertices = fill_number_of_vertices(
            intersected_vertices, origin_vertices_size
        )

        orientation = compute_orientation_from_polyline(
            non_intersecting_vertices[:, :2]
        )  # function only works with 2d vertices
        orientation_dif = [
            abs(orientation[i + 1] - orientation[i]) for i in range(len(orientation) - 1)
        ]
        while np.isclose(np.max(orientation_dif), np.pi, 0.01):
            idx = np.argmax(orientation_dif)
            non_intersecting_vertices[idx + 1] = (
                non_intersecting_vertices[idx] + non_intersecting_vertices[idx + 2]
            ) / 2
            orientation = compute_orientation_from_polyline(
                non_intersecting_vertices[:, :2]
            )  # function only works with 2d vertices
            orientation_dif = [
                orientation[i + 1] - orientation[i] for i in range(len(orientation) - 1)
            ]

        if is_left:
            lanelet.left_vertices = non_intersecting_vertices
        else:
            lanelet.right_vertices = non_intersecting_vertices

    def _repair_normal_adjacency(self, location: Tuple[int, int], is_left: bool, is_same: bool):
        """
        Repairs polylines_left_same_dir_parallel_adj, polylines_left_opposite_dir_parallel_adj,
        polylines_right_same_dir_parallel_adj, and polylines_right_opposite_dir_parallel_adj. The polylines of lanelet
        and adjacency are averaged and equalized.

        :param location: Location of invalid state.
        :param is_left: Boolean indicates whether the inequality of left or right polyline and polyline of adjacency
        should be considered.
        :param is_same: Boolean indicates whether the same or opposite direction of adjacency should be considered.
        """

        def get_vertices():
            if is_left:
                lan_vertices = lanelet.left_vertices
                if is_same:
                    adj_vertices = adjacency.right_vertices
                else:
                    adj_vertices = adjacency.left_vertices
            else:
                lan_vertices = lanelet.right_vertices
                if is_same:
                    adj_vertices = adjacency.left_vertices
                else:
                    adj_vertices = adjacency.right_vertices
            return lan_vertices, adj_vertices

        lanelet_id, adjacency_id = location

        lanelet = self._network.find_lanelet_by_id(lanelet_id)
        adjacency = self._network.find_lanelet_by_id(adjacency_id)

        lanelet_vertices, adjacency_vertices = get_vertices()

        lan_size = len(lanelet_vertices)
        adj_size = len(adjacency_vertices)

        if lan_size > adj_size:
            adjacency._right_vertices = fill_number_of_vertices(adjacency.right_vertices, lan_size)
            adjacency._left_vertices = fill_number_of_vertices(adjacency.left_vertices, lan_size)
        elif lan_size < adj_size:
            lanelet._right_vertices = fill_number_of_vertices(lanelet.right_vertices, adj_size)
            lanelet._left_vertices = fill_number_of_vertices(lanelet.left_vertices, adj_size)

        lanelet_vertices, adjacency_vertices = get_vertices()

        avg_vertices = average_vertices(lanelet_vertices, adjacency_vertices, not is_same)

        lanelet_vertices[:] = avg_vertices

        if not is_same:
            avg_vertices = avg_vertices[::-1]
        adjacency_vertices[:] = avg_vertices

        self._optimal_vertice(
            lanelet_id, adjacency_id, lanelet_vertices, adjacency_vertices, True, is_same
        )
        self._optimal_vertice(
            lanelet_id, adjacency_id, lanelet_vertices, adjacency_vertices, False, not is_same
        )

    def _repair_connections_adjacency(
        self, location: Tuple[int, int], is_left_adj: bool, is_merging_adj: bool
    ):
        """
        Repairs connections_left_merging_adj, connections_right_merging_adj, connections_left_forking_adj,
        and connections_right_forking_adj. The affected connection points are averaged and equalized to lanelet
        and merging/forking adjacency.

        :param location: Location of invalid state.
        :param is_left_adj: Boolean indicates whether the left or right adjacency should be considered.
        """
        lanelet_id, adjacency_id = location

        lanelet = self._network.find_lanelet_by_id(lanelet_id)
        adjacency = self._network.find_lanelet_by_id(adjacency_id)

        is_start = is_merging_adj

        fst_vertices = lanelet.left_vertices
        snd_vertices = adjacency.left_vertices
        self._optimal_vertice(
            lanelet_id, adjacency_id, fst_vertices, snd_vertices, not is_start, not is_start
        )

        fst_vertices = lanelet.right_vertices
        snd_vertices = adjacency.right_vertices
        self._optimal_vertice(
            lanelet_id, adjacency_id, fst_vertices, snd_vertices, not is_start, not is_start
        )

        if is_left_adj:
            fst_vertices = lanelet.left_vertices
            snd_vertices = adjacency.right_vertices
        else:
            fst_vertices = lanelet.right_vertices
            snd_vertices = adjacency.left_vertices
        self._optimal_vertice(
            lanelet_id, adjacency_id, fst_vertices, snd_vertices, is_start, is_start
        )

    def _repair_possible_adjacency(self, location: Tuple[int, int], is_left: bool, is_same: bool):
        """
        Repairs potential_left_same_dir_parallel_adj, potential_left_opposite_dir_parallel_adj,
        potential_right_same_dir_parallel_adj, potential_right_opposite_dir_parallel_adj,
        potential_left_merging_adj, potential_right_merging_adj, potential_left_forking_adj,
        and potential_right_forking_adj. The potential adjacency is referenced from lanelet.

        :param location: Location of invalid state.
        :param is_left: Boolean indicates whether the left or right adjacency should be considered.
        """
        lanelet_id, adjacency_id = location

        lanelet = self._network.find_lanelet_by_id(lanelet_id)

        if is_left:
            lanelet.adj_left = adjacency_id
            lanelet.adj_left_same_direction = is_same
        else:
            lanelet.adj_right = adjacency_id
            lanelet.adj_right_same_direction = is_same
