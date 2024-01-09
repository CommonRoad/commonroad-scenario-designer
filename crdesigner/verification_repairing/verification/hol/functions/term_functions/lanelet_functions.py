from typing import List, Set

import numpy as np
from commonroad.scenario.lanelet import Lanelet, StopLine


def lanelet_id(lanelet: Lanelet) -> int:
    """
    Returns the ID of the lanelet.

    :param lanelet: Lanelet.
    :return: Lanelet ID.
    """
    return lanelet.lanelet_id


def left_adj(lanelet: Lanelet) -> int:
    """
    Returns the ID of the left adjacency.

    :param lanelet: Lanelet.
    :return: Lanelet ID.
    """
    return lanelet.adj_left


def right_adj(lanelet: Lanelet) -> int:
    """
    Returns the ID of the right adjacency.

    :param lanelet: Lanelet.
    :return: Lanelet ID.
    """
    return lanelet.adj_right


def left_polyline(lanelet: Lanelet) -> np.ndarray:
    """
    Returns the left polyline of the lanelet.

    :param lanelet: Lanelet.
    :return: Left polyline.
    """
    return lanelet.left_vertices


def right_polyline(lanelet: Lanelet) -> np.ndarray:
    """
    Returns the right polyline of the lanelet.

    :param lanelet: Lanelet.
    :return: Right polyline.
    """
    return lanelet.right_vertices


def start_vertex(polyline: np.ndarray) -> np.ndarray:
    """
    Returns the start vertex of the polyline.

    :param polyline: Polyline.
    :return: Start vertex.
    """
    return polyline[0]


def end_vertex(polyline: np.ndarray) -> np.ndarray:
    """
    Returns the end vertex of the polyline.

    :param polyline: Polyline.
    :return: End vertex.
    """
    return polyline[len(polyline) - 1]


def traffic_signs(lanelet: Lanelet) -> Set[int]:
    """
    Returns the IDs of all traffic signs referenced by the lanelet.

    :param lanelet: Lanelet.
    :return: IDs of traffic signs.
    """
    return lanelet.traffic_signs


def traffic_lights(lanelet: Lanelet) -> Set[int]:
    """
    Returns the IDs of all traffic lights referenced by the lanelet.

    :param lanelet: Lanelet.
    :return: IDs of traffic lights.
    """
    return lanelet.traffic_lights


def stop_line(lanelet: Lanelet) -> StopLine:
    """
    Returns the stop line of the lanelet.

    :param lanelet: Lanelet.
    :return: Stop line.
    """
    return lanelet.stop_line


def predecessors(lanelet: Lanelet) -> List[int]:
    """
    Returns the IDs of the predecessors of the lanelet.

    :param lanelet: Lanelet.
    :return: Predecessor IDs.
    """
    return lanelet.predecessor


def successors(lanelet: Lanelet) -> List[int]:
    """
    Returns the IDs of the successors of the lanelet.

    :param lanelet: Lanelet.
    :return: Successor IDs.
    """
    return lanelet.successor


def stop_line_traffic_signs(stop_line: StopLine) -> Set[int]:
    """
    Returns the IDs of the traffic signs of the stop line.

    :param stop_line: Stop line.
    :return: IDs of traffic signs.
    """
    return stop_line.traffic_sign_ref


def stop_line_traffic_lights(stop_line: StopLine) -> Set[int]:
    """
    Returns the IDs of the traffic lights of the stop line.

    :param stop_line: Stop line.
    :return: IDs of traffic lights.
    """
    return stop_line.traffic_light_ref
