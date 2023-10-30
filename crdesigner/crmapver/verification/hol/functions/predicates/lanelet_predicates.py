import numpy as np
from commonroad.scenario.lanelet import Lanelet, StopLine
from commonroad.scenario.traffic_sign import TrafficSign
from commonroad.scenario.traffic_light import TrafficLight
from shapely import LineString
from similaritymeasures import similaritymeasures


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


def is_left_adj_same_direction(lanelet: Lanelet) -> bool:
    """
    Checks whether the left adjacency of the lanelet has the same direction.

    :param lanelet: Lanelet.
    :return: Boolean indicates whether the left adjacency of the lanelet has the same direction.
    """
    return lanelet.adj_left_same_direction


def is_right_adj_same_direction(lanelet: Lanelet) -> bool:
    """
    Checks whether the right adjacency of the lanelet has the same direction.

    :param lanelet: Lanelet.
    :return: Boolean indicates whether the right adjacency of the lanelet has the same direction.
    """
    return lanelet.adj_right_same_direction


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
    line_0 = [(x, y) for x, y in polyline_0]
    line_1 = [(x, y) for x, y in polyline_1]

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
    line = [(x, y) for x, y in polyline]
    line_string = LineString(line)

    return not line_string.is_simple


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
    if not ((np.linalg.norm(polyline_0[0] - polyline_1[0]) < 1)
            and (np.linalg.norm((polyline_0[-1] - polyline_1[-1]) < 1))
            or ((np.linalg.norm(polyline_0[0] - polyline_1[-1]) < 1)
                and (np.linalg.norm(polyline_0[-1] - polyline_1[0]) < 1))):
        return False
    # length is completely different
    if (Lanelet._compute_polyline_cumsum_dist([polyline_0])[-1] -
            Lanelet._compute_polyline_cumsum_dist([polyline_1])[-1] > 50):
        return False
    # all vertices are quite close
    if (polyline_0.shape[0] == polyline_1.shape[0] and
            all([dist < 0.01 for dist in np.linalg.norm(polyline_0 - polyline_1, axis=1)])):
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
    parallel, merging, forking = 'parallel', 'merging', 'forking'

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
