import itertools
import logging
from collections import Counter

import numpy as np
from commonroad.scenario.lanelet import Lanelet, StopLine
from commonroad.scenario.traffic_light import TrafficLight
from commonroad.scenario.traffic_sign import TrafficSign
from commonroad_clcs.clcs import CurvilinearCoordinateSystem
from commonroad_clcs.config import CLCSParams, ResamplingParams
from commonroad_clcs.util import (
    chaikins_corner_cutting,
    compute_orientation_from_polyline,
    resample_polyline,
)
from shapely import LineString
from similaritymeasures import similaritymeasures

from crdesigner.common.config.lanelet2_config import Lanelet2Config


def has_left_adj_ref(lanelet: Lanelet) -> bool:
    """
    Checks whether the lanelet has a reference to a left adjacency.

    :param lanelet: Lanelet.
    :return: Boolean indicates whether the lanelet has a reference to a left adjacency.
    """
    return lanelet.adj_left is not None


def has_right_adj_ref(lanelet: Lanelet) -> bool:
    """
    Checks whether the lanelet has a reference to a right adjacency.

    :param lanelet: Lanelet.
    :return: Boolean indicates whether the lanelet has a reference to a right adjacency.
    """
    return lanelet.adj_right is not None


def has_left_adj(lanelet_0: Lanelet, lanelet_1: Lanelet) -> bool:
    """
    Checks whether the first lanelet references the second lanelet as left adjacency.

    :param lanelet_0: First lanelet.
    :param lanelet_1: Second lanelet.
    :return: Boolean indicates whether the first lanelet references the second lanelet as left adjacency.
    """
    return lanelet_0.adj_left == lanelet_1.lanelet_id


def has_right_adj(lanelet_0: Lanelet, lanelet_1: Lanelet) -> bool:
    """
    Checks whether th first lanelet references the second lanelet as right adjacency.

    :param lanelet_0: First lanelet.
    :param lanelet_1: Second lanelet.
    :return: Boolean indicates whether the first lanelet references the second lanelet as right adjacency.
    """
    return lanelet_0.adj_right == lanelet_1.lanelet_id


def is_left_adj_same_direction(lanelet: Lanelet, adj_lanelet: Lanelet) -> bool:
    """
    Checks whether the left adjacency of the lanelet has the same direction.

    :param lanelet: Lanelet.
    :param adj_lanelet: Potential adjacent lanelet.
    :return: Boolean indicates whether the left adjacency of the lanelet has the same direction.
    """
    return (
        lanelet.adj_left_same_direction
        and np.linalg.norm(lanelet.left_vertices[0] - adj_lanelet.right_vertices[0]) < 1
        and np.linalg.norm(lanelet.left_vertices[-1] - adj_lanelet.right_vertices[-1]) < 1
    )


def is_left_adj_opposite_direction(lanelet: Lanelet, adj_lanelet: Lanelet) -> bool:
    """
    Checks whether the left adjacency of the lanelet has the same direction.

    :param lanelet: Lanelet.
    :param adj_lanelet: Potential adjacent lanelet.
    :return: Boolean indicates whether the left adjacency of the lanelet has the same direction.
    """
    return (
        not lanelet.adj_left_same_direction
        and np.linalg.norm(lanelet.left_vertices[0] - adj_lanelet.left_vertices[-1]) < 1
        and np.linalg.norm(lanelet.left_vertices[-1] - adj_lanelet.left_vertices[0]) < 1
    )


def is_right_adj_same_direction(lanelet: Lanelet, adj_lanelet: Lanelet) -> bool:
    """
    Checks whether the right adjacency of the lanelet has the same direction.

    :param lanelet: Lanelet.
    :param adj_lanelet: Potential adjacent lanelet.
    :return: Boolean indicates whether the right adjacency of the lanelet has the same direction.
    """
    return (
        lanelet.adj_right_same_direction
        and np.linalg.norm(lanelet.right_vertices[0] - adj_lanelet.left_vertices[0]) < 1
        and np.linalg.norm(lanelet.right_vertices[-1] - adj_lanelet.left_vertices[-1]) < 1
    )


def is_right_adj_opposite_direction(lanelet: Lanelet, adj_lanelet: Lanelet) -> bool:
    """
    Checks whether the right adjacency of the lanelet has the opposite direction.

    :param lanelet: Lanelet.
    :param adj_lanelet: Potential adjacent lanelet.
    :return: Boolean indicates whether the right adjacency of the lanelet has the same direction.
    """
    return (
        not lanelet.adj_right_same_direction
        and np.linalg.norm(lanelet.right_vertices[0] - adj_lanelet.right_vertices[-1]) < 1
        and np.linalg.norm(lanelet.right_vertices[-1] - adj_lanelet.right_vertices[0]) < 1
    )


def is_correct_left_right_boundary_assignment(lanelet: Lanelet) -> bool:
    """
    Checks whether the boundaries of two polylines are swapped.

    :param lanelet: Lanelet.
    :return: Boolean indicates whether the two boundaries should be swapped.
    """
    return not _wrong_left_right_boundary_side(
        lanelet.center_vertices, lanelet.left_vertices, lanelet.right_vertices
    )


def _wrong_left_right_boundary_side(
    center_vertices: np.ndarray,
    left_vertices: np.ndarray,
    right_vertices: np.ndarray,
    config: Lanelet2Config = Lanelet2Config(),
) -> bool:
    """
    Checks whether left and right boundary are swapped.

    :param center_vertices: Center vertices of lanelet.
    :param left_vertices: Left boundary of lanelet.
    :param right_vertices: Right boundary of lanelet.
    :returns: Boolean indicating whether boundaries are swapped.
    """
    left, right = None, None
    center_vertices = chaikins_corner_cutting(center_vertices, config.chaikins_initial_refinements)
    center_vertices = resample_polyline(center_vertices, config.resampling_initial_step)
    for eps, max_polyline_resampling_step in itertools.product(
        config.eps2_values, config.max_polyline_resampling_step_values
    ):
        try:
            if len(center_vertices) == 2:
                center_vertices = np.insert(
                    center_vertices, 1, (center_vertices[0] + center_vertices[1]) / 2, axis=0
                )
            cpar = CLCSParams(
                eps2=eps,
                resampling=ResamplingParams(
                    fixed_step=max_polyline_resampling_step, interpolation_type="linear"
                ),
            )
            ccs = CurvilinearCoordinateSystem(center_vertices, cpar, False)
            left = np.array(
                [ccs.convert_to_curvilinear_coords(vert[0], vert[1])[1] for vert in left_vertices]
            )
            right = np.array(
                [ccs.convert_to_curvilinear_coords(vert[0], vert[1])[1] for vert in right_vertices]
            )
            break
        except Exception:
            center_vertices = chaikins_corner_cutting(
                center_vertices, config.chaikins_repeated_refinements
            )
            center_vertices = resample_polyline(center_vertices, config.resampling_repeated_step)
            continue

    # >= since we use the function also for the lanelet2cr conversion where it might be
    # that start/ending vertices of forks/merges match
    return sum(left - right >= 0) / len(left) < config.perc_vert_wrong_side


def has_predecessor(lanelet_0: Lanelet, lanelet_1: Lanelet) -> bool:
    """
    Checks whether the first lanelet references the second lanelet as predecessor.

    :param lanelet_0: First lanelet.
    :param lanelet_1: Second lanelet.
    :return: Boolean indicates whether the first lanelet references the second lanelet as predecessor.
    """
    return lanelet_1.lanelet_id in lanelet_0.predecessor


def has_successor(lanelet_0: Lanelet, lanelet_1: Lanelet) -> bool:
    """
    Checks whether the first lanelet references the second lanelet as successor.

    :param lanelet_0: First lanelet.
    :param lanelet_1: Second lanelet.
    :return: Boolean indicates whether the first lanelet references the second lanelet as successor.
    """
    return lanelet_1.lanelet_id in lanelet_0.successor


def has_traffic_sign(lanelet: Lanelet, traffic_sign: TrafficSign) -> bool:
    """
    Checks whether the lanelet references the traffic sign.

    :param lanelet: Lanelet.
    :param traffic_sign: Traffic sign.
    :return: Boolean indicates whether the lanelet references the traffic sign.
    """
    return traffic_sign.traffic_sign_id in lanelet.traffic_signs


def has_traffic_light(lanelet: Lanelet, traffic_light: TrafficLight) -> bool:
    """
    Checks whether the lanelet references the traffic light.

    :param lanelet: Lanelet.
    :param traffic_light: Traffic light.
    :return: Boolean indicates whether the lanelet references the traffic light.
    """
    return traffic_light.traffic_light_id in lanelet.traffic_lights


def is_polylines_intersection(polyline_0: np.ndarray, polyline_1: np.ndarray) -> bool:
    """
    Checks whether two polylines intersect each other.

    :param polyline_0: First polyline.
    :param polyline_1: Second lanelet.
    :return: Boolean indicates whether two polylines intersect each other.
    """
    line_0 = [(x, y, z[0]) if z else (x, y) for x, y, *z in polyline_0]
    line_1 = [(x, y, z[0]) if z else (x, y) for x, y, *z in polyline_1]

    line_string_0 = LineString(line_0)
    line_string_1 = LineString(line_1)

    result = line_string_0.intersection(line_string_1)

    return not result.is_empty


def is_polyline_self_intersection(polyline: np.ndarray):
    """
    Checks whether the polyline intersects itself.

    :param polyline: Polyline.
    :return: Boolean indicates whether the polyline intersects itself.
    """
    line = [(x, y, z[0]) if z else (x, y) for x, y, *z in polyline]
    orientation = compute_orientation_from_polyline(
        polyline[:, :2]
    )  # function does not support 3d vertices
    orientation_dif = [
        abs(orientation[i + 1] - orientation[i]) for i in range(len(orientation) - 1)
    ]
    line_string = LineString(line)

    # shapely does not detect all cases of self-intersections:
    # second check: twice the same element
    # third check: 180 degree orientation change of line; visually line is perfect
    return (
        not line_string.is_simple
        or Counter(line).most_common(1)[0][1] > 1
        or np.isclose(np.max(orientation_dif), np.pi)
    )


def are_equal_vertices(vertex_0: np.ndarray, vertex_1: np.ndarray) -> bool:
    """
    Checks whether two vertices are equal.

    :param vertex_0: First vertex.
    :param vertex_1: Second vertex.
    :return: Boolean indicates whether two vertices are equal.
    """
    return np.linalg.norm(vertex_0 - vertex_1) < 1e-5  # TODO: Support config threshold


def are_intersected_lanelets(lanelet_0: Lanelet, lanelet_1: Lanelet) -> bool:
    """
    Checks whether the first and the second lanelet intersect each other.

    :param lanelet_0: First lanelet.
    :param lanelet_1: Second lanelet.
    :return: Boolean indicates whether the first and the second lanelet intersect each other.
    """
    result = lanelet_0.polygon.shapely_object.intersection(lanelet_1.polygon.shapely_object)

    return result.is_empty


def has_stop_line(lanelet: Lanelet):
    """
    Checks whether the lanelet has a stop line.

    :param lanelet: Lanelet.
    :return: Boolean indicates whether the lanelet has a stop line
    """
    return lanelet.stop_line is not None


def has_start_point(stop_line: StopLine) -> bool:
    """
    Checks whether the stop line has a start point.

    :param stop_line: Stop line.
    :return: Boolean indicates whether the stop line has a start point.
    """
    return stop_line.start is not None


def has_end_point(stop_line: StopLine) -> bool:
    """
    Checks whether the stop line has an end point.

    :param stop_line: Stop line.
    :return: Boolean indicates whether the stop line has an end point.
    """
    return stop_line.end is not None


def are_similar_polylines(polyline_0: np.ndarray, polyline_1: np.ndarray) -> bool:
    """
    Checks the similarity of two polylines.

    :param polyline_0: First polyline symbol.
    :param polyline_1: Second polyline symbol.
    :return: Boolean symbol indicates whether the two polylines are similar.
    """
    # initial or final vertices are not similar
    if not (
        (np.linalg.norm(polyline_0[0] - polyline_1[0]) < 1)
        and (np.linalg.norm((polyline_0[-1] - polyline_1[-1]) < 1))
        or (
            (np.linalg.norm(polyline_0[0] - polyline_1[-1]) < 1)
            and (np.linalg.norm(polyline_0[-1] - polyline_1[0]) < 1)
        )
    ):
        return False
    # length is completely different
    if (
        Lanelet._compute_polyline_cumsum_dist([polyline_0])[-1]
        - Lanelet._compute_polyline_cumsum_dist([polyline_1])[-1]
        > 50
    ):
        return False
    # all vertices are quite close
    if polyline_0.shape[0] == polyline_1.shape[0] and all(
        [dist < 0.01 for dist in np.linalg.norm(polyline_0 - polyline_1, axis=1)]
    ):
        return True
    return similaritymeasures.frechet_dist(polyline_0, polyline_1) < 1e-6
    # TODO: Use thresh of config and update parameter above in this function


def is_adj_type(lanelet: Lanelet, adj: Lanelet, exp_adj_type: str) -> bool:
    """
    Identifies the type of adjacency of lanelet. The types include parallel, merging, and forking adjacencies.

    :param lanelet: Lanelet.
    :param adj: Adjacency.
    :param exp_adj_type: Expected adjacent type.
    :return: Boolean indicates whether the expected adjacent type is equal to the computed type.
    """
    parallel, merging, forking = "parallel", "merging", "forking"

    is_left = lanelet.adj_left == adj.lanelet_id

    if is_left:
        is_same_dir = lanelet.adj_left_same_direction
    else:
        is_same_dir = lanelet.adj_right_same_direction

    if not is_same_dir:
        return parallel == exp_adj_type

    if is_left:  # TODO: Shift part to utils script to avoid duplications
        adj_poly = adj.right_vertices
    else:
        adj_poly = adj.left_vertices

    left_poly = lanelet.left_vertices
    right_poly = lanelet.right_vertices

    adj_size = len(adj_poly)
    lan_size = len(left_poly)

    left_start_dist = np.linalg.norm(left_poly[0] - adj_poly[0])
    left_end_dist = np.linalg.norm(left_poly[lan_size - 1] - adj_poly[adj_size - 1])

    right_start_dist = np.linalg.norm(right_poly[0] - adj_poly[0])
    right_end_dist = np.linalg.norm(right_poly[lan_size - 1] - adj_poly[adj_size - 1])

    if left_start_dist > right_start_dist and left_end_dist < right_end_dist:
        adj_type = forking if is_left else merging
    elif left_start_dist < right_start_dist and left_end_dist > right_end_dist:
        adj_type = merging if is_left else forking
    else:
        adj_type = parallel

    return adj_type == exp_adj_type
