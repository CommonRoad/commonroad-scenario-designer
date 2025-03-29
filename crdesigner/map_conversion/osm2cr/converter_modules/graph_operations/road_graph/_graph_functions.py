"""
functions used for graph
"""

from queue import Queue
from typing import List, Set, Tuple

import numpy as np

from crdesigner.common.config.osm_config import osm_config as config
from crdesigner.map_conversion.common import geometry
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations.road_graph._graph_edge import (
    GraphEdge,
)
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations.road_graph._graph_lane import (
    Lane,
)
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations.road_graph._graph_node import (
    GraphNode,
)


def graph_search(center_node: GraphNode) -> Tuple[Set[GraphNode], Set[GraphEdge]]:
    """
    searches all elements connected to center_node from a graph and returns them

    :param center_node: the node to search from
    :return: a tuple of all nodes and edges found
    """
    nodes = set()
    edges = set()
    explore = Queue()
    explore.put(center_node)
    while not explore.empty():
        node = explore.get()
        if node:
            for edge in node.edges:
                if edge not in edges:
                    edges.add(edge)
                    if edge.node1 not in nodes:
                        explore.put(edge.node1)
                        nodes.add(edge.node1)
                    if edge.node2 not in nodes:
                        explore.put(edge.node2)
                        nodes.add(edge.node2)
    return nodes, edges


def find_adjacents(newlane: Lane, lanes: Set[Lane]) -> Set[Lane]:
    """
    finds all adjacent lanes to newlane

    :param newlane: lane to find adjacent lanes
    :param lanes: already found adjacent lanes
    :return: set of all adjacent lanes
    """
    adding = set()
    lanes.add(newlane)
    if newlane.adjacent_left is not None and newlane.adjacent_left not in lanes:
        adding.add(newlane.adjacent_left)
    if newlane.adjacent_right is not None and newlane.adjacent_right not in lanes:
        adding.add(newlane.adjacent_right)
    for element in adding:
        lanes |= find_adjacents(element, lanes)
    return lanes


def sort_adjacent_lanes(lane: Lane) -> Tuple[List[Lane], List[bool]]:
    """
    sorts the adjacent lanes as they are in edges

    :param lane: start lane to sort
    :return: tuple of: 1. sorted list of lanes, 2. bool list of which is true for forward directed lanes
    """
    result = [lane]
    forward = [True]
    # find lanes right of this
    next_right = lane.adjacent_right
    next_right_is_forward = lane.adjacent_right_direction_equal
    while next_right is not None:
        result.append(next_right)
        forward.append(next_right_is_forward)
        if next_right_is_forward:
            next_right_is_forward = next_right.adjacent_right_direction_equal
            next_right = next_right.adjacent_right
        else:
            next_right_is_forward = not next_right.adjacent_left_direction_equal
            next_right = next_right.adjacent_left
    # find lanes left of this
    next_left = lane.adjacent_left
    next_left_is_forward = lane.adjacent_left_direction_equal
    while next_left is not None:
        result = [next_left] + result
        forward = [next_left_is_forward] + forward
        if next_left_is_forward:
            next_left_is_forward = next_left.adjacent_left_direction_equal
            next_left = next_left.adjacent_left
        else:
            next_left_is_forward = not next_left.adjacent_right_direction_equal
            next_left = next_left.adjacent_right
    assert len(result) == len(find_adjacents(lane, set()))
    assert set(result) == find_adjacents(lane, set())
    assert len(forward) == len(result)
    return result, forward


def get_lane_waypoints(
    nr_of_lanes: int, width: float, center_waypoints: List[np.ndarray]
) -> List[List[np.ndarray]]:
    """
    creates waypoints of lanes based on a center line and the width and count of lanes

    :param nr_of_lanes: count of lanes
    :param width: width of lanes
    :param center_waypoints: List of waypoints specifying the center course
    :return: List of Lists of waypoints
    """
    waypoints = []
    if nr_of_lanes % 2 == 0:
        left, right = geometry.create_parallels(center_waypoints, width / 2)
        waypoints = [left, right]
        for i in range(int((nr_of_lanes - 2) / 2)):
            waypoints.append(geometry.create_parallels(waypoints[-1], width)[1])
        for i in range(int((nr_of_lanes - 2) / 2)):
            waypoints.insert(0, geometry.create_parallels(waypoints[0], width)[0])
    else:
        waypoints.append(center_waypoints)
        for i in range(int(nr_of_lanes / 2)):
            waypoints.append(geometry.create_parallels(waypoints[-1], width)[1])
        for i in range(int(nr_of_lanes / 2)):
            waypoints.insert(0, geometry.create_parallels(waypoints[0], width)[0])
    return waypoints


def set_points(predecessor: Lane, successor: Lane) -> List[np.ndarray]:
    """
    sets the waypoints of a link segment between two lanes

    :param predecessor: the preceding lane
    :param successor: the successive lane
    :return: list of waypoints
    """
    point_distance = config.INTERPOLATION_DISTANCE_INTERNAL
    d = config.BEZIER_PARAMETER
    p1 = predecessor.waypoints[-1]
    p4 = successor.waypoints[0]
    vector1 = p1 - predecessor.waypoints[-2]
    vector1 = vector1 / np.linalg.norm(vector1) * np.linalg.norm(p1 - p4) * d
    p2 = p1 + vector1
    vector2 = p4 - successor.waypoints[1]
    vector2 = vector2 / np.linalg.norm(vector2) * np.linalg.norm(p1 - p4) * d
    p3 = p4 + vector2
    n = max(int(np.linalg.norm(p1 - p4) / point_distance), 2)
    a1, a2, intersection_point = geometry.intersection(p1, p4, vector1, vector2)
    # check if intersection point could be created and the vectors intersect, else use cubic bezier
    if intersection_point is None:
        waypoints = geometry.evaluate_bezier(np.array([p1, p2, p3, p4]), n)
        waypoints.append(p4)
        return waypoints
    # use quadratic bezier if possible
    # do not use it if intersection point is to close to start or end point
    distance_to_points = min(
        np.linalg.norm(intersection_point - p1), np.linalg.norm(intersection_point - p4)
    )
    total_distance = np.linalg.norm(p1 - p4)
    if not (distance_to_points > 1 or distance_to_points / total_distance > 0.1):
        pass
    if a1 > 0 and a2 > 0 and (distance_to_points > 1 or distance_to_points / total_distance > 0.1):
        waypoints = geometry.evaluate_bezier(np.array([p1, intersection_point, p4]), n)
        waypoints.append(p4)
    # else use cubic bezier
    else:
        waypoints = geometry.evaluate_bezier(np.array([p1, p2, p3, p4]), n)
        waypoints.append(p4)
    return waypoints
