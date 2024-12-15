"""
This module holds all methods necessary to cluster segments at intersections.
"""

from typing import Dict, List, Set, Tuple

import numpy as np

from crdesigner.common.config.osm_config import osm_config as config
from crdesigner.map_conversion.common import geometry
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations.road_graph._graph import (
    Graph,
)
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations.road_graph._graph_edge import (
    GraphEdge,
)
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations.road_graph._graph_functions import (
    get_lane_waypoints,
    set_points,
)
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations.road_graph._graph_lane import (
    Lane,
)
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations.road_graph._graph_node import (
    GraphNode,
)


def lane_at_start_of_edge(edge: GraphEdge, lane: Lane) -> bool:
    """
    checks if lane starts at start or end of an edge

    :param edge: the edge to check
    :param lane: the lane to check
    :return: true if lane starts at start of edge, false if it ends there
    """
    if edge.node1 == lane.from_node or edge.node1 == lane.to_node:
        return True
    elif edge.node2 == lane.from_node or edge.node2 == lane.to_node:
        return False
    else:
        raise ValueError("lane and edge have no node in common")


def get_lane_point(lane: Lane, at_start: bool) -> np.ndarray:
    """
    gets the first or last waypoint of a lane

    :param lane: the lane
    :param at_start: specifies if first or last point is returned
    :return: the respective way point
    """
    if lane.forward != at_start:
        point = lane.waypoints[-1]
    else:
        point = lane.waypoints[0]
    return point


def alladjacent(lanes: List[Lane]) -> bool:
    """
    checks if all lanes in the list are adjacent

    :param lanes: list of lanes
    :return: true if all lanes in the list are adjacent, else false
    """
    adjacents = set()
    for lane in lanes:
        adjacents.add(lane.adjacent_left)
        adjacents.add(lane.adjacent_right)
    for lane in lanes:
        if lane not in adjacents:
            return False
    return True


def find_groups(graph: Graph) -> Dict[int, Set[Lane]]:
    """
    finds group of link segments heading between two different nodes

    :param graph: the graph
    :return: dicionary of groups
    """
    segments = graph.lanelinks.copy()
    groups = {}
    for segment in segments:
        node1 = segment.get_node(True)
        node2 = segment.get_node(False)
        if node1 != node2 and node1.get_distance(node2) > config.CLUSTER_LENGTH:
            # segment.forward = node1.id < node2.id
            if node1.id < node2.id:
                group_id = int(str(node1.id) + str(node2.id))
            else:
                group_id = int(str(node2.id) + str(node1.id))
            if group_id in groups:
                groups[group_id].add(segment)
            else:
                groups[group_id] = {segment}
    return groups


def group_segments_to_links(
    groups: Dict[int, Set[Lane]], group_id: int
) -> Tuple[Dict[int, Set[Lane]], Dict[GraphEdge, Set[int]]]:
    """
    groups segments in a group by the edges they connect -> links
    assigns all links to the edges they connect

    :param groups: all groups
    :param group_id: the id of the group to divide in subsets
    :return: links: the subsets of groups connecting two edges, edge_links the connections of edges
    """
    links = {}
    edge_links = {}
    for segment in groups[group_id]:
        edge1 = next(iter(segment.predecessors)).edge
        edge2 = next(iter(segment.successors)).edge
        if edge1.id < edge2.id:
            link_id = int(str(edge1.id) + str(edge2.id))
        else:
            link_id = int(str(edge2.id) + str(edge1.id))
        if link_id in links:
            links[link_id].add(segment)
        else:
            links[link_id] = {segment}
        for edge in (edge1, edge2):
            if edge in edge_links:
                edge_links[edge].add(link_id)
            else:
                edge_links[edge] = {link_id}
    return links, edge_links


def get_start_point(current_lanes: List[Lane], at_start: bool) -> np.ndarray:
    """
    gets the start point of the cluster

    :param current_lanes: lanes that will be extended by the cluster
    :param at_start: specifies if lanes will be extended at start or end
    :return: the start point
    """
    if len(current_lanes) % 2 == 0:
        lane1 = current_lanes[int(len(current_lanes) / 2) - 1]
        point1 = get_lane_point(lane1, at_start)
        lane2 = current_lanes[int(len(current_lanes) / 2)]
        point2 = get_lane_point(lane2, at_start)
        start_point = (point1 + point2) / 2
    else:
        lane = current_lanes[int(len(current_lanes) / 2)]
        start_point = get_lane_point(lane, at_start)
    return start_point


def get_end_point(start_point: np.ndarray, node2: GraphNode) -> np.ndarray:
    """
    gets the end point of the cluster

    :param start_point: the start point of the cluster
    :param node2: the node, the cluster leads to
    :return: the end point
    """
    vector = node2.get_cooridnates() - start_point
    length = np.linalg.norm(vector)
    distance = max(config.INTERSECTION_DISTANCE, node2.get_highest_edge_distance())
    newlength = length - distance
    vector = vector / length * newlength
    end_point = start_point + vector
    return end_point


def get_middle_point(
    start_point: np.ndarray,
    end_point: np.ndarray,
    edge: GraphEdge,
    node1: GraphNode,
) -> np.ndarray:
    """
    gets the central control point for the bezier curve of the cluster

    :param start_point: the start point of the cluster
    :param end_point:  the end point of the cluster
    :param edge: the extended edge
    :param node1: the node at which the edge starts
    :return: the central control point
    """
    edge_waypoints = edge.interpolated_waypoints
    if edge.node1 == node1:
        vector1 = edge_waypoints[0] - edge_waypoints[1]
    elif edge.node2 == node1:
        vector1 = edge_waypoints[-1] - edge_waypoints[-2]
    else:
        raise ValueError("edge is not at node 1")
    vector1 = (
        vector1
        / np.linalg.norm(vector1)
        * np.linalg.norm(start_point - end_point)
        * config.BEZIER_PARAMETER
    )
    middle_point = start_point + vector1
    return middle_point


def get_waypoints_of_group(
    start_point: np.ndarray, end_point: np.ndarray, middle_point: np.ndarray
) -> List[np.ndarray]:
    """
    gets the way points for the course of the cluster

    :param start_point: the start point of the cluster
    :param end_point: the end point of the cluster
    :param middle_point: the central control point of the cluster
    :return: list of way points
    """
    point_distance = config.INTERPOLATION_DISTANCE_INTERNAL
    n = max(int(np.linalg.norm(start_point - end_point) / point_distance), 2)
    bezier_points = np.array([start_point, middle_point, end_point])
    waypoints = geometry.evaluate_bezier(bezier_points, n)
    waypoints.append(end_point)
    return waypoints


def get_nodes(at_start: bool, edge: GraphEdge, segment: Lane) -> Tuple[GraphNode, GraphNode]:
    """
    gets nodes which are connected by cluster

    :param at_start: true if the cluster is at the start of the edge
    :param edge: the edge on which the cluster is placed
    :param segment: a segment of the cluster
    :return: the nodes which are connected by the cluster
    """
    if at_start:
        node1 = edge.node1
    else:
        node1 = edge.node2
    if segment.from_node == node1:
        node2 = segment.to_node
    elif segment.to_node == node1:
        node2 = segment.from_node
    else:
        raise ValueError("segment is not at node")
    return node1, node2


def find_lanes_to_extend(
    edge: GraphEdge, current_segments: Set[Lane], at_start: bool
) -> List[Lane]:
    """
    finds lanes of an edge which are consecutive with current_segments

    :param edge: lanes on this edge will be searched
    :param current_segments: the segments to be clustered
    :param at_start: true if current_segments are at the start of edge, else false
    :return: list of lanes of edge, which are consecutive to current_segments
    """
    current_lanes = []
    for lane in edge.lanes:
        if lane.forward != at_start:
            if lane.successors & current_segments:
                current_lanes.append(lane)
        else:
            if lane.predecessors & current_segments:
                current_lanes.append(lane)
    return current_lanes


def create_new_lanes(
    current_lanes: List[Lane], current_segments: Set[Lane], at_start: bool
) -> List[Lane]:
    """
    creates new link segments for the segment

    :param current_lanes: the lanes of the edge which will be extended
    :param current_segments: the segments at the intersection
    :param at_start: true if cluster will be created at start of the edge
    :return: new created link segments
    """
    new_lanes = []
    for lane in current_lanes:
        predecessors = {lane}
        successors = set()
        if at_start == lane.forward:
            predecessors, successors = successors, predecessors
            node = lane.to_node
        else:
            node = lane.from_node
        if at_start:
            width1 = width2 = lane.width1
        else:
            width1 = width2 = lane.width2
        new_lane = Lane(
            None,
            successors,
            predecessors,
            "none",
            width1,
            width2,
            node,
            node,
            lane.speedlimit,
        )
        # set predecessors and successors of segments and new lane correctly
        if new_lane.predecessors:
            predecessor = next(iter(new_lane.predecessors))
            successor_segments = predecessor.successors & current_segments
            predecessor.successors -= successor_segments
            predecessor.successors.add(new_lane)
            for successor_segment in successor_segments:
                successor_segment.predecessors = {new_lane}
                new_lane.successors.add(successor_segment)
            new_lane.forward = predecessor.forward
        elif new_lane.successors:
            successor = next(iter(new_lane.successors))
            predecessor_segments = successor.predecessors & current_segments
            successor.predecessors -= predecessor_segments
            successor.predecessors.add(new_lane)
            for predecessor_segment in predecessor_segments:
                predecessor_segment.successors = {new_lane}
                new_lane.predecessors.add(predecessor_segment)
            new_lane.forward = successor.forward
        new_lanes.append(new_lane)

    # set adjacents correctly
    for index, lane in enumerate(new_lanes[:-1]):
        next_lane = new_lanes[index + 1]
        if lane.forward:
            lane.adjacent_right = next_lane
            lane.adjacent_right_direction_equal = lane.forward == next_lane.forward
        else:
            lane.adjacent_left = next_lane
            lane.adjacent_left_direction_equal = lane.forward == next_lane.forward
    for index, lane in enumerate(new_lanes[1:]):
        prev_lane = new_lanes[index]
        if lane.forward:
            lane.adjacent_left = prev_lane
            lane.adjacent_left_direction_equal = lane.forward == prev_lane.forward
        else:
            lane.adjacent_right = prev_lane
            lane.adjacent_right_direction_equal = lane.forward == prev_lane.forward

    return new_lanes


def set_waypoints_of_lanes(
    edge: GraphEdge, new_lanes: List[Lane], waypoints: List[np.ndarray]
) -> None:
    """
    sets waypoints of new created link segments

    :param edge: the extended edge
    :param new_lanes: the new created link segments
    :param waypoints: the central course of the cluster
    :return: None
    """
    width = config.LANEWIDTHS[edge.roadtype]
    lane_waypoints = get_lane_waypoints(len(new_lanes), width, waypoints)
    for index, lane in enumerate(new_lanes):
        # lane.waypoints = lane_waypoints[index]
        if lane.forward:
            lane.waypoints = lane_waypoints[index]
        else:
            lane.waypoints = lane_waypoints[index][::-1]
    return


def set_waypoints_of_segments(current_segments: Set[Lane]) -> None:
    """
    updates waypoints of link segments segments

    :param current_segments: the updated segments
    :return: None
    """
    for segment in current_segments:
        predecessor = next(iter(segment.predecessors))
        successor = next(iter(segment.successors))
        waypoints = set_points(predecessor, successor)
        segment.waypoints = waypoints
    return


def cluster_segments(graph: Graph) -> None:
    """
    groups segments in a graph to clusters

    :param graph: graph
    :return: None
    """
    # find groups of lane segments
    groups = find_groups(graph)
    for group_id in groups:
        # group segments into links
        links, edge_links = group_segments_to_links(groups, group_id)
        for edge in edge_links:
            link_ids = edge_links[edge]
            if len(link_ids) > 1:
                segment = next(iter(links[next(iter(link_ids))]))
                at_start = lane_at_start_of_edge(edge, segment)
                # get nodes
                node1, node2 = get_nodes(at_start, edge, segment)
                # get current Segments
                current_segments = set()
                for link_id in link_ids:
                    for segment in links[link_id]:
                        current_segments.add(segment)
                # find lanes of edge that wil be extended
                current_lanes = find_lanes_to_extend(edge, current_segments, at_start)
                # only go on if all extended lanes are adjacent
                if not alladjacent(current_lanes):
                    continue
                # get the start point
                start_point = get_start_point(current_lanes, at_start)
                # get the end point
                end_point = get_end_point(start_point, node2)
                # get the middle point
                middle_point = get_middle_point(start_point, end_point, edge, node1)
                if at_start:
                    start_point, end_point = end_point, start_point
                # create waypoints of group
                waypoints = get_waypoints_of_group(start_point, end_point, middle_point)
                # only go on if new lanes would be long enough
                if np.linalg.norm(start_point - end_point) < config.LEAST_CLUSTER_LENGTH:
                    continue
                # create new lanes
                new_lanes = create_new_lanes(current_lanes, current_segments, at_start)
                # create waypoints for lanes
                set_waypoints_of_lanes(edge, new_lanes, waypoints)
                # add new lanes to graph
                graph.lanelinks |= set(new_lanes)
                # set segment waypoints new
                set_waypoints_of_segments(current_segments)
    return
