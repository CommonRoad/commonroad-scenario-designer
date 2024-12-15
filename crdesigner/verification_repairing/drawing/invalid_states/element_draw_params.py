from abc import ABC
from typing import Any, Dict, Tuple

from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.visualization.draw_params import LaneletParams


class ElementDrawParams(ABC):
    def __init__(self, network: LaneletNetwork):
        self._network = network

        self._draw_params = {}
        self._custom_draw_params = {}

    @property
    def draw_params(self):
        return self._draw_params

    @property
    def custom_draw_params(self):
        return self._custom_draw_params

    def _update_custom_draw_params(self, lanelet_id: int, custom_params: Dict[str, Any]):
        """
        Updates the custom drawing parameters.

        :param lanelet_id: Lanelet ID.
        :param custom_params: Custom parameters.
        """
        if lanelet_id in self._custom_draw_params.keys():
            custom_params.update(self._custom_draw_params[lanelet_id])
        self._custom_draw_params[lanelet_id] = custom_params


class LaneletDrawParams(ElementDrawParams):
    def __init__(self, network: LaneletNetwork):
        super(LaneletDrawParams, self).__init__(network)

    def param_unique_id(self, location: Tuple[int]):
        """
        Inserts drawing params for unique_id.

        :param location: Location of invalid state.
        """
        (lanelet_id,) = location

        self._insert_common_lanelet_params(lanelet_id)

    def param_same_vertices_size(self, location: Tuple[int]):
        """
        Inserts drawing params for same_vertices_size.

        :param location: Location of invalid state.
        """
        (lanelet_id,) = location

        self._insert_common_lanelet_params(lanelet_id)

    def param_vertices_more_than_one(self, location: Tuple[int]):
        """
        Inserts drawing params for vertices_more_than_one.

        :param location: Location of invalid state.
        """
        (lanelet_id,) = location

        self._insert_common_lanelet_params(lanelet_id)

    def param_existence_left_adj(self, location: Tuple[int]):
        """
        Inserts drawing params for existence_left_adj.

        :param location: Location of invalid state.
        """
        (lanelet_id,) = location

        self._insert_common_lanelet_params(lanelet_id)

    def param_existence_right_adj(self, location: Tuple[int]):
        """
        Inserts drawing params for existence_right_adj.

        :param location: Location of invalid state.
        """
        (lanelet_id,) = location

        self._insert_common_lanelet_params(lanelet_id)

    def param_existence_predecessor(self, location: Tuple[int, int]):
        """
        Inserts drawing params for existence_left_adj.

        :param location: Location of invalid state.
        """
        lanelet_id, _ = location

        self._insert_common_lanelet_params(lanelet_id)

    def param_existence_successor(self, location: Tuple[int, int]):
        """
        Inserts drawing params for existence_left_adj.

        :param location: Location of invalid state.
        """
        lanelet_id, _ = location

        self._insert_common_lanelet_params(lanelet_id)

    def param_connections_predecessor(self, location: Tuple[int, int]):
        """
        Inserts drawing params for connections_predecessor.

        :param location: Location of invalid state.
        """
        lanelet_id, predecessor_id = location

        self._insert_common_lanelet_params(lanelet_id)
        self._insert_vertex_marking_params(
            lanelet_id, left_start_vertex=True, right_start_vertex=True
        )
        self._insert_vertex_marking_params(
            predecessor_id, left_end_vertex=True, right_end_vertex=True
        )

    def param_connections_successor(self, location: Tuple[int, int]):
        """
        Inserts drawing params for connections_successor.

        :param location: Location of invalid state.
        """
        lanelet_id, successor_id = location

        self._insert_common_lanelet_params(lanelet_id)
        self._insert_vertex_marking_params(lanelet_id, left_end_vertex=True, right_end_vertex=True)
        self._insert_vertex_marking_params(
            successor_id, left_start_vertex=True, right_start_vertex=True
        )

    def param_polylines_left_same_dir_parallel_adj(self, location: Tuple[int, int]):
        """
        Inserts drawing params for polylines_left_same_dir_parallel_adj.

        :param location: Location of invalid state.
        """
        lanelet_id, adj_id = location

        self._insert_common_lanelet_params(lanelet_id)
        self._insert_bound_params(lanelet_id, left_bound=True)

    def param_polylines_left_opposite_dir_parallel_adj(self, location: Tuple[int, int]):
        """
        Inserts drawing params for polylines_left_opposite_dir_parallel_adj.

        :param location: Location of invalid state.
        """
        lanelet_id, adj_id = location

        self._insert_common_lanelet_params(lanelet_id)
        self._insert_bound_params(lanelet_id, left_bound=True)

    def param_polylines_right_same_dir_parallel_adj(self, location: Tuple[int, int]):
        """
        Inserts drawing params for polylines_right_same_dir_parallel_adj.

        :param location: Location of invalid state.
        """
        lanelet_id, adj_id = location

        self._insert_common_lanelet_params(lanelet_id)
        self._insert_bound_params(lanelet_id, right_bound=True)

    def param_polylines_right_opposite_dir_parallel_adj(self, location: Tuple[int, int]):
        """
        Inserts drawing params for polylines_right_opposite_dir_parallel_adj.

        :param location: Location of invalid state.
        """
        lanelet_id, adj_id = location

        self._insert_common_lanelet_params(lanelet_id)
        self._insert_bound_params(lanelet_id, right_bound=True)

    def param_connections_left_merging_adj(self, location: Tuple[int, int]):
        """
        Inserts drawing params for connections_left_merging_adj.

        :param location: Location of invalid state.
        """
        lanelet_id, adj_id = location

        self._insert_common_lanelet_params(lanelet_id)
        self._insert_vertex_marking_params(
            lanelet_id, left_start_vertex=True, left_end_vertex=True, right_end_vertex=True
        )
        self._insert_vertex_marking_params(
            adj_id, right_start_vertex=True, left_end_vertex=True, right_end_vertex=True
        )

    def param_connections_right_merging_adj(self, location: Tuple[int, int]):
        """
        Inserts drawing params for connections_right_merging_adj.

        :param location: Location of invalid state.
        """
        lanelet_id, adj_id = location

        self._insert_common_lanelet_params(lanelet_id)
        self._insert_vertex_marking_params(
            lanelet_id, left_start_vertex=True, left_end_vertex=True, right_end_vertex=True
        )
        self._insert_vertex_marking_params(
            adj_id, left_start_vertex=True, left_end_vertex=True, right_end_vertex=True
        )

    def param_connections_left_forking_adj(self, location: Tuple[int, int]):
        """
        Inserts drawing params for connections_left_forking_adj.

        :param location: Location of invalid state.
        """
        lanelet_id, adj_id = location

        self._insert_common_lanelet_params(lanelet_id)
        self._insert_vertex_marking_params(
            lanelet_id, left_start_vertex=True, right_start_vertex=True, left_end_vertex=True
        )
        self._insert_vertex_marking_params(
            adj_id, left_start_vertex=True, right_start_vertex=True, right_end_vertex=True
        )

    def param_connections_right_forking_adj(self, location: Tuple[int, int]):
        """
        Inserts drawing params for connections_right_forking_adj.

        :param location: Location of invalid state.
        """
        lanelet_id, adj_id = location

        self._insert_common_lanelet_params(lanelet_id)
        self._insert_vertex_marking_params(
            lanelet_id, left_start_vertex=True, right_start_vertex=True, right_end_vertex=True
        )
        self._insert_vertex_marking_params(
            adj_id, left_start_vertex=True, right_start_vertex=True, left_end_vertex=True
        )

    def param_potential_successor(self, location: Tuple[int, int]):
        """
        Inserts drawing params for potential_successor.

        :param location: Location of invalid state.
        """
        lanelet_id, successor_id = location

        self._insert_common_lanelet_params(lanelet_id)
        self._insert_vector_params(lanelet_id, successor_id)

    def param_potential_predecessor(self, location: Tuple[int, int]):
        """
        Inserts drawing params for potential_predecessor.

        :param location: Location of invalid state.
        """
        lanelet_id, predecessor_id = location

        self._insert_common_lanelet_params(lanelet_id)
        self._insert_vector_params(lanelet_id, predecessor_id)

    def param_potential_left_same_dir_parallel_adj(self, location: Tuple[int, int]):
        """
        Inserts drawing params for potential_left_same_dir_parallel_adj.

        :param location: Location of invalid state.
        """
        lanelet_id, left_adj_id = location

        self._insert_common_lanelet_params(lanelet_id)
        self._insert_vector_params(lanelet_id, left_adj_id)

    def param_potential_left_opposite_dir_parallel_adj(self, location: Tuple[int, int]):
        """
        Inserts drawing params for potential_left_opposite_dir_parallel_adj.

        :param location: Location of invalid state.
        """
        lanelet_id, left_adj_id = location

        self._insert_common_lanelet_params(lanelet_id)
        self._insert_vector_params(lanelet_id, left_adj_id)

    def param_potential_right_same_dir_parallel_adj(self, location: Tuple[int, int]):
        """
        Inserts drawing params for potential_right_same_dir_parallel_adj.

        :param location: Location of invalid state.
        """
        lanelet_id, right_adj_id = location

        self._insert_common_lanelet_params(lanelet_id)
        self._insert_vector_params(lanelet_id, right_adj_id)

    def param_potential_right_opposite_dir_parallel_adj(self, location: Tuple[int, int]):
        """
        Inserts drawing params for potential_right_opposite_dir_parallel_adj.

        :param location: Location of invalid state.
        """
        lanelet_id, right_adj_id = location

        self._insert_common_lanelet_params(lanelet_id)
        self._insert_vector_params(lanelet_id, right_adj_id)

    def param_potential_left_merging_adj(self, location: Tuple[int, int]):
        """
        Inserts drawing params for potential_left_merging_adj.

        :param location: Location of invalid state.
        """
        lanelet_id, left_adj_id = location

        self._insert_common_lanelet_params(lanelet_id)
        self._insert_vector_params(lanelet_id, left_adj_id)

    def param_potential_right_merging_adj(self, location: Tuple[int, int]):
        """
        Inserts drawing params for potential_right_merging_adj.

        :param location: Location of invalid state.
        """
        lanelet_id, right_adj_id = location

        self._insert_common_lanelet_params(lanelet_id)
        self._insert_vector_params(lanelet_id, right_adj_id)

    def param_potential_left_forking_adj(self, location: Tuple[int, int]):
        """
        Inserts drawing params for potential_left_forking_adj.

        :param location: Location of invalid state.
        """
        lanelet_id, left_adj_id = location

        self._insert_common_lanelet_params(lanelet_id)
        self._insert_vector_params(lanelet_id, left_adj_id)

    def param_potential_right_forking_adj(self, location: Tuple[int, int]):
        """
        Inserts drawing params for potential_right_forking_adj.

        :param location: Location of invalid state.
        """
        lanelet_id, right_adj_id = location

        self._insert_common_lanelet_params(lanelet_id)
        self._insert_vector_params(lanelet_id, right_adj_id)

    def param_non_predecessor_as_successor(self, location: Tuple[int, int]):
        """
        Inserts drawing params for non_predecessor_as_successor.

        :param location: Location of invalid state.
        """
        lanelet_id, _ = location

        self._insert_common_lanelet_params(lanelet_id)

    def param_non_successor_as_predecessor(self, location: Tuple[int, int]):
        """
        Inserts drawing params for non_successor_as_predecessor.

        :param location: Location of invalid state.
        """
        lanelet_id, _ = location

        self._insert_common_lanelet_params(lanelet_id)

    def param_polylines_intersection(self, location: Tuple[int]):
        """
        Inserts drawing params for polylines_intersection.

        :param location: Location of invalid state.
        """
        (lanelet_id,) = location

        self._insert_common_lanelet_params(lanelet_id)
        self._draw_params[lanelet_id].left_bound_color = "red"
        self._draw_params[lanelet_id].right_bound_color = "red"

    def param_left_self_intersection(self, location: Tuple[int]):
        """
        Inserts drawing params for left_self_intersection.

        :param location: Location of invalid state.
        """
        (lanelet_id,) = location

        self._insert_common_lanelet_params(lanelet_id)
        self._draw_params[lanelet_id].left_bound_color = "red"

    def param_right_self_intersection(self, location: Tuple[int]):
        """
        Inserts drawing params for right_self_intersection.

        :param location: Location of invalid state.
        """
        (lanelet_id,) = location

        self._insert_common_lanelet_params(lanelet_id)
        self._draw_params[lanelet_id].right_bound_color = "red"

    def param_non_followed_composable_lanelets(self, location: Tuple[int, int]):
        """
        Inserts drawing params for non_followed_composable_lanelets.

        :param location: Location of invalid state.
        """
        lanelet_id, successor_id = location

        self._insert_common_lanelet_params(lanelet_id)
        self._insert_common_lanelet_params(successor_id)

    def param_referenced_intersecting_lanelets(self, location: Tuple[int, int]):
        """
        Inserts drawing params for referenced_intersecting_lanelets.

        :param location: Location of invalid state.
        """
        pass

    def param_existence_traffic_signs(self, location: Tuple[int, int]):
        """
        Inserts drawing params for existence_traffic_signs.

        :param location: Location of invalid state.
        """
        lanelet_id, _ = location

        self._insert_common_lanelet_params(lanelet_id)

    def param_existence_traffic_lights(self, location: Tuple[int, int]):
        """
        Inserts drawing params for existence_traffic_lights.

        :param location: Location of invalid state.
        """
        lanelet_id, _ = location

        self._insert_common_lanelet_params(lanelet_id)

    def param_existence_stop_line_traffic_signs(self, location: Tuple[int, int]):
        """
        Inserts drawing params for existence_stop_line_traffic_signs.

        :param location: Location of invalid state.
        """
        lanelet_id, _ = location

        self._insert_common_lanelet_params(lanelet_id)
        self._draw_params[lanelet_id].stop_line_color = "red"

    def param_existence_stop_line_traffic_lights(self, location: Tuple[int, int]):
        """
        Inserts drawing params for existence_stop_line_traffic_lights.

        :param location: Location of invalid state.
        """
        lanelet_id, _ = location

        self._insert_common_lanelet_params(lanelet_id)
        self._draw_params[lanelet_id].stop_line_color = "red"

    def param_included_stop_line_traffic_signs(self, location: Tuple[int, int]):
        """
        Inserts drawing params for included_stop_line_traffic_signs.

        :param location: Location of invalid state.
        """
        lanelet_id, _ = location

        self._insert_common_lanelet_params(lanelet_id)
        self._draw_params[lanelet_id].stop_line_color = "red"

    def param_included_stop_line_traffic_lights(self, location: Tuple[int, int]):
        """
        Inserts drawing params for included_stop_line_traffic_lights.

        :param location: Location of invalid state.
        """
        lanelet_id, _ = location

        self._insert_common_lanelet_params(lanelet_id)
        self._draw_params[lanelet_id].stop_line_color = "red"

    def param_zero_or_two_points_stop_line(self, location: Tuple[int]):
        """
        Inserts drawing params for zero_or_two_points_stop_line.

        :param location: Location of invalid state.
        """
        (lanelet_id,) = location

        self._insert_common_lanelet_params(lanelet_id)
        self._draw_params[lanelet_id].stop_line_color = "red"

    def param_stop_line_points_on_polylines(self, location: Tuple[int]):
        """
        Inserts drawing params for stop_line_points_on_polylines.

        :param location: Location of invalid state.
        """
        (lanelet_id,) = location

        self._insert_common_lanelet_params(lanelet_id)
        self._draw_params[lanelet_id].stop_line_color = "red"

    def _insert_common_lanelet_params(self, lanelet_id: int):
        """
        Inserts the common drawing params for an invalid state in lanelet.

        :param lanelet_id: Lanelet ID.
        """
        if lanelet_id not in self._draw_params.keys():
            self._draw_params[lanelet_id] = LaneletParams()
        self._draw_params[lanelet_id].facecolor = "lightcoral"
        self._draw_params[lanelet_id].fill_lanelet = True

    def _insert_bound_params(
        self, lanelet_id: int, left_bound: bool = False, right_bound: bool = False
    ):
        """
        Inserts drawing params for polylines_left_same_dir_parallel_adj, polylines_right_same_dir_parallel_adj,
        polylines_left_opposite_dir_parallel_adj, and polylines_right_opposite_dir_parallel_adj.

        :param lanelet_id: Lanelet ID.
        :param left_bound: Boolean indicates whether the left boundary should be marked.
        :param right_bound: Boolean indicates whether the right boundary should be marked.
        """
        default_color = "#555555"
        mark_color = "red"

        self._draw_params[lanelet_id].left_bound_color = mark_color if left_bound else default_color
        self._draw_params[lanelet_id].right_bound_color = (
            mark_color if right_bound else default_color
        )
        self._draw_params[lanelet_id].draw_linewidth = 1.5

    def _insert_vertex_marking_params(
        self,
        lanelet_id: int,
        left_start_vertex: bool = False,
        right_start_vertex: bool = False,
        left_end_vertex: bool = False,
        right_end_vertex: bool = False,
    ):
        """
        Inserts drawing params for connections_predecessor, connections_successor, connections_left_merging_adj,
        connections_right_merging_adj, connections_left_forking_adj and connections_right_forking_adj.

        :param lanelet_id: Lanelet ID.
        :param left_start_vertex: Boolean indicates whether the left start vertex should be marked.
        :param right_start_vertex: Boolean indicates whether the right start vertex should be marked.
        :param left_end_vertex: Boolean indicates whether the left end vertex should be marked.
        :param right_end_vertex: Boolean indicates whether the right end vertex should be marked.
        """

        params = {
            "mark_left_start_vertex": left_start_vertex,
            "mark_right_start_vertex": right_start_vertex,
            "mark_left_end_vertex": left_end_vertex,
            "mark_right_end_vertex": right_end_vertex,
        }

        self._update_custom_draw_params(lanelet_id, params)

    def _insert_vector_params(self, lanelet_id: int, other_lanelet_id: int):
        """
        Inserts drawing params for potential_successor, potential_predecessor,
        potential_left_same_dir_parallel_adj, potential_left_opposite_dir_parallel_adj,
        potential_right_same_dir_parallel_adj, potential_right_opposite_dir_parallel_adj,
        potential_left_merging_adj, potential_right_merging_adj, potential_left_forking_adj, and
        potential_right_forking_adj.

        :param lanelet_id: Lanelet ID.
        :param other_lanelet_id: Other lanelet ID.
        """
        lanelet = self._network.find_lanelet_by_id(lanelet_id)
        other_lanelet = self._network.find_lanelet_by_id(other_lanelet_id)

        params = {"show_vector": [lanelet.polygon.center, other_lanelet.polygon.center]}

        self._update_custom_draw_params(lanelet_id, params)


class TrafficSignDrawParams(ElementDrawParams):
    def __init__(self, network: LaneletNetwork):
        super(TrafficSignDrawParams, self).__init__(network)

    def param_at_least_one_traffic_sign_element(self, location: Tuple[int]):
        """
        Inserts drawing params for at_least_one_traffic_sign_element.

        :param location: Location of invalid state.
        """
        (traffic_sign_id,) = location

        self._insert_common_traffic_sign_params(traffic_sign_id)

    def param_referenced_traffic_sign(self, location: Tuple[int]):
        """
        Inserts drawing params for referenced_traffic_sign.

        :param location: Location of invalid state.
        """
        (traffic_sign_id,) = location

        self._insert_common_traffic_sign_params(traffic_sign_id)

    def param_given_additional_value(self, location: Tuple[int, int]):
        """
        Inserts drawing params for given_additional_value.

        :param location: Location of invalid state.
        """
        traffic_sign_id, _ = location

        self._insert_common_traffic_sign_params(traffic_sign_id)

    def param_valid_additional_value_speed_sign(self, location: Tuple[int, int]):
        """
        Inserts drawing params for valid_additional_value_speed_sign.

        :param location: Location of invalid state.
        """
        traffic_sign_id, _ = location

        self._insert_common_traffic_sign_params(traffic_sign_id)

    def param_maximal_distance_from_lanelet(self, location: Tuple[int]):
        """
        Inserts drawing params for maximal_distance_from_lanelet.

        :param location: Location of invalid state.
        """
        (traffic_sign_id,) = location

        self._insert_common_traffic_sign_params(traffic_sign_id)

    def _insert_common_traffic_sign_params(self, traffic_sign_id: int):
        """
        Inserts the common drawing params for an invalid state in traffic sign.

        :param traffic_sign_id: Traffic sign ID.
        """
        self._update_custom_draw_params(
            traffic_sign_id, {"mark_traffic_sign": True, "show_traffic_sign_id": True}
        )


class TrafficLightDrawParams(ElementDrawParams):
    def __init__(self, network: LaneletNetwork):
        super(TrafficLightDrawParams, self).__init__(network)

    def param_at_least_one_cycle_element(self, location: Tuple[int]):
        """
        Inserts drawing params for at_least_one_cycle_element.

        :param location: Location of invalid state.
        """
        (traffic_light_id,) = location

        self._insert_common_traffic_light_params(traffic_light_id)

    def param_traffic_light_per_incoming(self, location: Tuple[int, int, int]):
        """
        Inserts drawing params for traffic_light_per_incoming.

        :param location: Location of invalid state.
        """
        traffic_light_id, _, _ = location

        self._insert_common_traffic_light_params(traffic_light_id)

    def param_referenced_traffic_light(self, location: Tuple[int]):
        """
        Inserts drawing params for referenced_traffic_light.

        :param location: Location of invalid state.
        """
        (traffic_light_id,) = location

        self._insert_common_traffic_light_params(traffic_light_id)

    def param_non_zero_duration(self, location: Tuple[int]):
        """
        Inserts drawing params for non_zero_duration.

        :param location: Location of invalid state.
        """
        (traffic_light_id,) = location

        self._insert_common_traffic_light_params(traffic_light_id)

    def param_unique_state_in_cycle(self, location: Tuple[int, int]):
        """
        Inserts drawing params for unique_state_in_cycle.

        :param location: Location of invalid state.
        """
        traffic_light_id, _ = location

        self._insert_common_traffic_light_params(traffic_light_id)

    def param_cycle_state_combinations(self, location: Tuple[int]):
        """
        Inserts drawing params for cycle_state_combinations.

        :param location: Location of invalid state.
        """
        (traffic_light_id,) = location

        self._insert_common_traffic_light_params(traffic_light_id)

    def _insert_common_traffic_light_params(self, traffic_light_id: int):
        """
        Inserts the common drawing params for an invalid state in traffic light.

        :param traffic_light_id: Traffic light ID.
        """
        self._update_custom_draw_params(
            traffic_light_id, {"mark_traffic_light": True, "show_traffic_light_id": True}
        )


class IntersectionDrawParams(ElementDrawParams):
    def __init__(self, network: LaneletNetwork):
        super(IntersectionDrawParams, self).__init__(network)

    def param_at_least_two_incoming_elements(self, location: Tuple[int]):
        """
        Inserts drawing params for at_least_two_incoming_elements.

        :param location: Location of invalid state.
        """
        pass

    def param_at_least_one_incoming_lanelet(self, location: Tuple[int, int]):
        """
        Inserts drawing params for at_least_one_incoming_lanelet.

        :param location: Location of invalid state.
        """
        pass

    def param_existence_is_left_of(self, location: Tuple[int, int]):
        """
        Inserts drawing params for existence_is_left_of.

        :param location: Location of invalid state.
        """
        pass

    def param_existence_incoming_lanelets(self, location: Tuple[int, int, int]):
        """
        Inserts drawing params for existence_incoming_lanelets.

        :param location: Location of invalid state.
        """
        pass
