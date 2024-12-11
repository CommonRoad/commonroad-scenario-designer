from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List, Optional, Set, Tuple

import numpy as np
from ordered_set import OrderedSet
from pyproj import Transformer

from crdesigner.common.config.osm_config import osm_config as config
from crdesigner.map_conversion.common import geometry

from ._graph_edge import GraphEdge
from ._graph_functions import (
    find_adjacents,
    get_lane_waypoints,
    graph_search,
    set_points,
    sort_adjacent_lanes,
)
from ._graph_lane import Lane
from ._graph_node import GraphNode
from ._graph_traffic_light import GraphTrafficLight
from ._graph_traffic_sign import GraphTrafficSign

if TYPE_CHECKING:
    from ...osm_operations.osm_parser import Bounds


class Graph:
    def __init__(
        self,
        nodes: Set[GraphNode],
        edges: Set[GraphEdge],
        center_point: Tuple[float, float],
        bounds: Bounds,
        transformer: Transformer,
        traffic_signs: List[GraphTrafficSign],
        traffic_lights: List[GraphTrafficLight],
    ) -> None:
        """
        creates a new graph

        :param nodes: nodes of the graph
        :param edges: edges of the graph
        :return: None
        """
        self.nodes = nodes
        self.edges = edges
        self.center_point = center_point
        self.bounds = bounds
        self.transformer = transformer
        self.lanelinks: Set[Lane] = OrderedSet()
        self.traffic_signs = traffic_signs
        self.traffic_lights = traffic_lights

    def get_central_node(self) -> GraphNode:
        """
        finds the most central node in the graph

        :return: most central node
        """
        center_node = None
        min_distance = 0
        for node in self.nodes:
            distance = np.linalg.norm(np.array([node.x, node.y]))
            if center_node is None:
                center_node = node
                min_distance = distance
            elif distance < min_distance:
                min_distance = distance
                center_node = node
        return center_node

    def make_contiguous(self) -> None:
        """
        deletes all elements of the graph that are not connected with the central node

        :return: None
        """
        center_node = self.get_central_node()
        nodes, edges = graph_search(center_node)
        self.nodes, self.edges = nodes, edges

    def link_edges(self) -> None:
        """
        sets successors and predecessors for edges,
        according to the angle they have to each other at intersections

        :return: None
        """
        for node in self.nodes:
            if node.get_degree() > 1:
                edges = list(node.edges)
                for index, edge in enumerate(edges):
                    other_edges = edges[:index] + edges[index + 1 :]
                    angles = []
                    for other_edge in other_edges:
                        angles.append(edge.angle_to(other_edge, node))
                    link = other_edges[int(np.argmax(angles))]
                    angle = edge.angle_to(link, node)
                    if angle > 0.9 * np.pi:
                        # successor found
                        if edge.node1 == node:
                            edge.backward_successor = link
                        elif edge.node2 == node:
                            edge.forward_successor = link
                        else:
                            raise ValueError("graph is malformed")

    def create_lane_waypoints(self) -> None:
        """
        creates the waypoints of all lanes in the graph

        :return: None
        """
        for edge in self.edges:
            # width = config.LANEWIDTHS[edge.roadtype]
            width = edge.lanewidth
            waypoints = get_lane_waypoints(
                edge.nr_of_lanes, width, edge.get_interpolated_waypoints()
            )
            assert len(edge.lanes) == edge.nr_of_lanes
            assert len(waypoints) == len(edge.lanes)
            for index, lane in enumerate(edge.lanes):
                if lane.forward:
                    lane.waypoints = waypoints[index]
                else:
                    waypoints[index].reverse()
                    lane.waypoints = waypoints[index]
                if lane.waypoints is None:
                    raise ValueError("graph is malformed, waypoints are None")

    def interpolate(self) -> None:
        """
        interpolates all edges

        :return: None
        """
        for edge in self.edges:
            edge.get_interpolated_waypoints()
        return

    def crop_waypoints_at_intersections(self, intersection_dist: float) -> List[GraphEdge]:
        """
        crops all edges at intersections
        returns all edges that were too short for proper cropping

        :return: too short edges
        """
        edges_to_delete = []
        to_delete = []
        for node in self.nodes:
            if node.is_crossing:
                cropping_dist = intersection_dist / 10.0
            else:
                cropping_dist = intersection_dist
            node_point = np.array([node.x, node.y])
            node_edges = list(node.edges)
            for index, edge in enumerate(node_edges):
                distance = 0
                edgewaypoints = edge.get_interpolated_waypoints()
                if edge.points_to(node):
                    edgewaypoints = edgewaypoints[::-1]
                other_edges = node_edges[index + 1 :] + node_edges[:index]
                if len(other_edges) <= 0:
                    # this node has degree of 1 and does not need to be cropped
                    pass
                else:
                    for other_edge in other_edges:
                        otherwaypoints = other_edge.get_interpolated_waypoints()
                        if other_edge.points_to(node):
                            otherwaypoints = otherwaypoints[::-1]
                        i = 0
                        if config.INTERSECTION_CROPPING_WITH_RESPECT_TO_ROADS:
                            distance_to_edge = (
                                edge.get_width() / 2 + other_edge.get_width() / 2 + cropping_dist
                            )
                            while (
                                i < min(len(edgewaypoints), len(otherwaypoints))
                                and np.linalg.norm(edgewaypoints[i] - otherwaypoints[i])
                                < distance_to_edge
                            ):
                                i += 1
                        else:
                            while (
                                i < min(len(edgewaypoints), len(otherwaypoints))
                                and np.linalg.norm(edgewaypoints[i] - edgewaypoints[0])
                                < cropping_dist
                            ):
                                i += 1
                        if i >= len(edgewaypoints):
                            if edge not in edges_to_delete:
                                edges_to_delete.append(edge)
                        if i >= len(otherwaypoints):
                            if other_edge not in edges_to_delete:
                                edges_to_delete.append(other_edge)
                        i = min(i, len(edgewaypoints) - 1, len(otherwaypoints) - 1)
                        distance = max(distance, np.linalg.norm(edgewaypoints[i] - node_point))
                    to_delete.append((edge, distance, node))
        cropping = {}
        for edge, distance, node in to_delete:
            index1, index2 = edge.get_crop_index(node, distance)
            if edge in cropping:
                index1 = max(index1, cropping[edge][0])
                index2 = min(index2, cropping[edge][1])
                cropping[edge] = index1, index2
            else:
                cropping[edge] = (index1, index2)
        for edge in cropping:
            index1, index2 = cropping[edge]
            edge.crop(index1, index2, edges_to_delete)

        return edges_to_delete

    def remove_edge(self, edge: GraphEdge) -> None:
        """
        removes an edge from the graph

        :param edge: the edge to remove
        :return: None
        """
        self.edges -= {edge}

        edge.node1.edges -= {edge}
        edge.node2.edges -= {edge}
        for lane in edge.lanes:
            successors = lane.successors.copy()
            predecessors = lane.predecessors.copy()
            for successor in successors:
                successor.predecessors -= {lane}
            for predecessor in predecessors:
                predecessor.successors -= {lane}

    def add_edge(self, edge: GraphEdge) -> None:
        """
        adds an existing edge to the graph
        this edge must connect two nodes which are already in the graph

        :param edge: the edge to add
        :return: None
        """
        assert edge.node1 in self.nodes
        assert edge.node2 in self.nodes
        self.edges.add(edge)
        edge.node1.edges.add(edge)
        edge.node2.edges.add(edge)

        for lane in edge.lanes:
            successors = lane.successors.copy()
            predecessors = lane.predecessors.copy()
            for successor in successors:
                successor.predecessors.add(lane)
            for predecessor in predecessors:
                predecessor.successors.add(lane)

    def delete_edges(self, edges: List[GraphEdge]) -> None:
        """
        deletes edges and links predecessors of deleted lanes with successors

        :param edges: edges to delete
        :return: None
        """
        for edge in edges:
            self.edges -= OrderedSet([edge])
            edge.node1.edges -= OrderedSet([edge])
            edge.node2.edges -= OrderedSet([edge])

            for lane in edge.lanes:
                successors = lane.successors.copy()
                predecessors = lane.predecessors.copy()
                for successor in successors:
                    successor.predecessors |= predecessors
                    successor.predecessors -= OrderedSet([lane])
                for predecessor in predecessors:
                    predecessor.successors |= successors
                    predecessor.successors -= OrderedSet([lane])
                lane.successors = []
                lane.predecessors = []

    def set_adjacents(self) -> None:
        """
        sets all predecessors and successors for lanes assigned to an edge correctly
        sets the adjacent left and right lanes for all lane links correctly
        this method should only be called after creating link segments

        :return: None
        """
        # delete all old predecessors and successors
        for edge in self.edges:
            for lane in edge.lanes:
                lane.predecessors = OrderedSet()
                lane.successors = OrderedSet()
        # set all predecessors and successors correctly
        for lane in self.lanelinks:
            for successor in lane.successors:
                successor.predecessors.add(lane)
            for predecessor in lane.predecessors:
                predecessor.successors.add(lane)
        # set all adjacent lanes correctly
        for lane in self.lanelinks:
            # adjacent_left
            for predecessor in lane.predecessors:
                if predecessor is not None and predecessor.adjacent_left is not None:
                    if predecessor.adjacent_left.forward == predecessor.forward:
                        possible_adjacents = predecessor.adjacent_left.successors
                        forward = True
                    else:
                        possible_adjacents = predecessor.adjacent_left.predecessors
                        forward = False
                    for possible_adjacent in possible_adjacents:
                        if forward:
                            for successor in possible_adjacent.successors:
                                if successor.adjacent_right in lane.successors:
                                    lane.adjacent_left = possible_adjacent
                                    lane.adjacent_left_direction_equal = True
                        else:
                            for predecessor2 in possible_adjacent.predecessors:
                                if predecessor2.adjacent_left in lane.successors:
                                    lane.adjacent_left = possible_adjacent
                                    lane.adjacent_left_direction_equal = False
            # adjacent_right
            for predecessor in lane.predecessors:
                if predecessor is not None and predecessor.adjacent_right is not None:
                    if predecessor.adjacent_right.forward == predecessor.forward:
                        possible_adjacents = predecessor.adjacent_right.successors
                        forward = True
                    else:
                        possible_adjacents = predecessor.adjacent_right.predecessors
                        forward = False
                    for possible_adjacent in possible_adjacents:
                        if forward:
                            for successor in possible_adjacent.successors:
                                if successor.adjacent_left in lane.successors:
                                    lane.adjacent_right = possible_adjacent
                                    lane.adjacent_right_direction_equal = True
                        else:
                            for predecessor2 in possible_adjacent.predecessors:
                                if predecessor2.adjacent_right in lane.successors:
                                    lane.adjacent_right = possible_adjacent
                                    lane.adjacent_right_direction_equal = False

        # set forward
        def update_forward(lane: Lane, forward: bool):
            lane.forward = forward
            if lane.adjacent_right is not None and lane.adjacent_right.forward is None:
                update_forward(lane.adjacent_right, lane.adjacent_right_direction_equal == forward)
            if lane.adjacent_left is not None and lane.adjacent_left.forward is None:
                update_forward(lane.adjacent_left, lane.adjacent_left_direction_equal == forward)
            return

        for lane in self.lanelinks:
            if lane.forward is None:
                # update_forward(lane, True)
                pass

    def create_lane_link_segments(self) -> None:
        """
        creates link segments for all intersections
        this method should only be called once, when creating a scenario

        :return: None
        """
        for edge in self.edges:
            for lane in edge.lanes:
                for successor in lane.successors:
                    predecessor = lane
                    waypoints = set_points(predecessor, successor)
                    from_node = predecessor.to_node
                    to_node = successor.from_node
                    width1 = predecessor.width2
                    width2 = successor.width1
                    segment = Lane(
                        None,
                        {successor},
                        {predecessor},
                        "none",
                        width1,
                        width2,
                        from_node,
                        to_node,
                        predecessor.speedlimit,
                    )
                    segment.waypoints = waypoints

                    # segment is only added if it does not form a turn
                    if (
                        successor.edge != predecessor.edge
                        and geometry.curvature(waypoints) > config.LANE_SEGMENT_ANGLE
                    ):
                        self.lanelinks.add(segment)

        self.set_adjacents()

    def create_lane_bounds(self, interpolation_scale: Optional[float] = None) -> None:
        """
        creates bounds for all lanes in the graph
        filters out negligible way points

        :return: None
        """
        # nr of waypoints is set equal for all adjacent lanes
        if interpolation_scale is not None:
            assert (
                interpolation_scale <= 1
            ), "scaling up with this function does not make sense and is probably not what you want"

        # set number of way points equal for all adjacent lanes
        for edge in self.edges:
            min_nr = None
            max_nr = None
            for lane in edge.lanes:
                if min_nr is None:
                    min_nr = len(lane.waypoints)
                else:
                    min_nr = min(len(lane.waypoints), min_nr)
                if max_nr is None:
                    max_nr = len(lane.waypoints)
                else:
                    max_nr = max(len(lane.waypoints), max_nr)
            new_nr = (min_nr + max_nr) // 2
            if interpolation_scale is not None:
                new_nr = int(new_nr * interpolation_scale)
            for lane in edge.lanes:
                if new_nr != len(lane.waypoints):
                    lane.set_nr_of_way_points(new_nr)
        for link_lane in self.lanelinks:
            adjacents = find_adjacents(link_lane, OrderedSet())
            min_nr = None
            max_nr = None
            for lane in adjacents:
                if min_nr is None:
                    min_nr = len(lane.waypoints)
                else:
                    min_nr = min(len(lane.waypoints), min_nr)
                if max_nr is None:
                    max_nr = len(lane.waypoints)
                else:
                    max_nr = max(len(lane.waypoints), max_nr)
            new_nr = (min_nr + max_nr) // 2
            if interpolation_scale is not None:
                new_nr = int(new_nr * interpolation_scale)
            for lane in adjacents:
                if new_nr != len(lane.waypoints):
                    lane.set_nr_of_way_points(new_nr)

        # filter negligible points
        if config.FILTER:
            logging.info("filtering points")
            for edge in self.edges:
                lines = [
                    lane.waypoints if lane.forward else lane.waypoints[::-1] for lane in edge.lanes
                ]
                lines = geometry.pre_filter_points(lines)
                lines = geometry.filter_points(lines, config.COMPRESSION_THRESHOLD)
                for index, lane in enumerate(edge.lanes):
                    lane.waypoints = lines[index] if lane.forward else lines[index][::-1]
            visited = set()
            for lane_link in self.lanelinks:
                if lane_link in visited:
                    continue
                lane_list, forward = sort_adjacent_lanes(lane_link)
                visited |= set(lane_list)
                lines = [
                    lane.waypoints if forward[i] else lane.waypoints[::-1]
                    for i, lane in enumerate(lane_list)
                ]
                lines = geometry.pre_filter_points(lines)
                lines = geometry.filter_points(lines, config.COMPRESSION_THRESHOLD)
                for index, lane in enumerate(lane_list):
                    lane.waypoints = lines[index] if forward[index] else lines[index][::-1]

        # create_lane_bounds
        for lane in self.get_all_lanes():
            lane.create_bounds()

    def get_all_lanes(self) -> List[Lane]:
        """
        gets all lanes of the graph: lanes assigned to edges and lane links

        :return: all lanes of graph
        """
        lanes = []
        for edge in self.edges:
            lanes += edge.lanes
        lanes += self.lanelinks
        return lanes

    def correct_start_end_points(self) -> None:
        """
        set first and last points of lane correct (same as predecessors, successors, adjacents, ...)

        :return: None
        """
        for lane in self.get_all_lanes():
            # point at start and left
            start_left = [(lane, "startleft")]
            # point at start and right
            start_right = [(lane, "startright")]
            # point at end and left
            end_left = [(lane, "endleft")]
            # point at end and right
            end_right = [(lane, "endright")]

            # predecessors
            for predecessor in lane.predecessors:
                start_left.append((predecessor, "endleft"))
                start_right.append((predecessor, "endright"))
                # left adjacents of predecessors
                if predecessor.adjacent_left is not None:
                    if predecessor.adjacent_left_direction_equal:
                        start_left.append((predecessor.adjacent_left, "endright"))
                    else:
                        start_left.append((predecessor.adjacent_left, "startleft"))
                # right adjacents of predecessors
                if predecessor.adjacent_right is not None:
                    if predecessor.adjacent_right_direction_equal:
                        start_right.append((predecessor.adjacent_right, "endleft"))
                    else:
                        start_right.append((predecessor.adjacent_right, "startright"))
            # successors
            for successor in lane.successors:
                end_left.append((successor, "startleft"))
                end_right.append((successor, "startright"))
                # left adjacents of successors
                if successor.adjacent_left is not None:
                    if successor.adjacent_left_direction_equal:
                        end_left.append((successor.adjacent_left, "startright"))
                    else:
                        end_left.append((successor.adjacent_left, "endleft"))
                # right adjacents of successors
                if successor.adjacent_right is not None:
                    if successor.adjacent_right_direction_equal:
                        end_right.append((successor.adjacent_right, "startleft"))
                    else:
                        end_right.append((successor.adjacent_right, "endright"))
            # left adjacents
            if lane.adjacent_left is not None:
                if lane.adjacent_left_direction_equal:
                    start_left.append((lane.adjacent_left, "startright"))
                    end_left.append((lane.adjacent_left, "endright"))
                    # successors of left adjacents
                    for successor in lane.adjacent_left.successors:
                        end_left.append((successor, "startright"))
                    # predecessors of left adjacents
                    for predecessor in lane.adjacent_left.predecessors:
                        start_left.append((predecessor, "endright"))
                else:
                    start_left.append((lane.adjacent_left, "endleft"))
                    end_left.append((lane.adjacent_left, "startleft"))
                    # successors of left adjacents backwards
                    for successor in lane.adjacent_left.successors:
                        start_left.append((successor, "startleft"))
                    # predecessors of left adjacents backwards
                    for predecessor in lane.adjacent_left.predecessors:
                        end_left.append((predecessor, "endleft"))
            # right adjacents
            if lane.adjacent_right is not None:
                if lane.adjacent_right_direction_equal:
                    start_right.append((lane.adjacent_right, "startleft"))
                    end_right.append((lane.adjacent_right, "endleft"))
                    # successors of right adjacents
                    for successor in lane.adjacent_right.successors:
                        end_right.append((successor, "startleft"))
                    # predecessors of right adjacents
                    for predecessor in lane.adjacent_right.predecessors:
                        start_right.append((predecessor, "endleft"))
                else:
                    start_right.append((lane.adjacent_right, "endright"))
                    end_right.append((lane.adjacent_right, "startright"))
                    # successors of right adjacents backwards
                    for successor in lane.adjacent_right.successors:
                        start_right.append((successor, "startright"))
                    # predecessors of right adjacents backwards
                    for predecessor in lane.adjacent_right.predecessors:
                        end_right.append((predecessor, "endright"))

            for corner in [start_left, start_right, end_left, end_right]:
                points: List[np.ndarray] = []
                for current_lane, position in corner:
                    points.append(current_lane.get_point(position))
                same = True
                for index, point in enumerate(points[:-1]):
                    same = same and all(point == points[index + 1])
                if not same:
                    center = np.sum(np.array(points), axis=0) / len(points)
                    for current_lane, position in corner:
                        current_lane.set_point(position, center)

    def set_custom_interpolation(self, d_internal: float, d_desired: float):
        for lane in self.get_all_lanes():
            n = int(d_internal / d_desired * len(lane.waypoints))
            lane.set_nr_of_way_points(n)
            lane.create_bounds()

    def delete_node(self, node: GraphNode) -> None:
        """
        removes a node from the graph
        this is only possible, if the node has no assigned edges

        :param node: the node to delete
        :return: None
        """
        if node not in self.nodes:
            raise ValueError("the provided node is not contained in this graph")
        if len(node.edges) > 0:
            raise ValueError("the provided node has edges assigned to it")
        self.nodes.remove(node)

    def check_for_validity(self) -> bool:
        # TODO check the following things:
        #   - lane adjacents and predecessors/successors reference each other both
        #   - lane adjacents use identical points for common bound
        #   - common points of predecessors/successors are identical
        #   - directions of predecessors/successors are the same
        return False

    def apply_traffic_signs(self) -> None:
        # for each traffic sign:
        # add to node and roads and lanes
        for sign in self.traffic_signs:
            if sign.node is not None:
                sign.node.add_traffic_sign(sign)
            for edge in sign.edges:
                for sub_edge in edge:
                    sub_edge.add_traffic_sign(
                        sign,
                    )

    def apply_traffic_lights(self) -> None:
        # for each traffic light
        # find edges going to node
        for light in self.traffic_lights:
            edges = light.node.edges
            for edge in edges:
                if light.forward and edge.node2.id == light.node.id:
                    edge.add_traffic_light(light, light.forward)
                if not light.forward and edge.node1.id == light.node.id:
                    edge.add_traffic_light(light, light.forward)

    def find_invalid_lanes(self) -> List[Lane]:
        """
        checks every lane for validity, using the shapely_object.is_valid method

        :return: List of invalid lanes
        """
        invalid_lanes = []
        for lane in self.get_all_lanes():
            if not lane.convert_to_polygon().shapely_object.is_valid:
                invalid_lanes.append(lane)
        return invalid_lanes

    def delete_lane(self, lane) -> None:
        """
        removes given lane from the graph

        :param lanes_to_delete: the lane to delete
        :return: None
        """
        # remove pre/suc relations
        for pre in lane.predecessors:
            pre.successors.remove(lane)
        for suc in lane.successors:
            suc.predecessors.remove(lane)

        # remove lane
        if lane in self.lanelinks:
            self.lanelinks.remove(lane)
        for edge in self.edges:
            if lane in edge.lanes:
                edge.lanes.remove(lane)

        # remove adjacent lane references
        for adj_lane in self.get_all_lanes():
            if adj_lane.adjacent_left is not None:
                if adj_lane.adjacent_left == lane:
                    adj_lane.adjacent_left = None
                    adj_lane.adjacent_left_direction_equal = None
            if adj_lane.adjacent_right is not None:
                if adj_lane.adjacent_right == lane:
                    adj_lane.adjacent_right = None
                    adj_lane.adjacent_right_direction_equal = None

    def delete_invalid_lanes(self) -> None:
        """
        finds and deletes invalid lanes in the RoadGraph

        :return: None
        """
        invalid_lanes = self.find_invalid_lanes()
        for lane in invalid_lanes:
            self.delete_lane(lane)
        # self.set_adjacents()

    def find_closest_edge_by_lat_lng(self, lat_lng, direction=None) -> GraphNode:
        """
        finds the closest GraphEdge in Graph to a given lat_lng tuple/list and a optional direction

        :param1 lat_lng: np.array storing latitude and longitude
        :param2 direction: optional filter to only return edge with corresponding direction
        :return: GraphEdge which is closest to the given lat_lng coordinates
        """
        given_point = self.transformer.transform(lat_lng[0], lat_lng[1])
        given_point = np.array(given_point)
        edges = list(self.edges)

        # edge coordinates need to be converted to lat lng before comparsion
        points = list()
        points_to_edge = dict()
        for edge in edges:
            edge_orientation = edge.get_compass_degrees()
            if direction is None or abs(edge_orientation - direction) < 60:  # degrees threshold
                for waypoint in edge.get_waypoints():
                    points.append(waypoint)
                    points_to_edge[tuple(waypoint)] = edge
        try:
            points = np.asarray(points)
            # https://codereview.stackexchange.com/a/28210
            dist_2 = np.sum((points - given_point) ** 2, axis=1)
            closest_edge_index = np.argmin(dist_2)
            found_point = points[closest_edge_index]

            # recalculate if direction input moves signs more than 20m away from its original found position
            if direction is not None and geometry.distance(found_point, [given_point]) > 0.0002:
                return self.find_closest_edge_by_lat_lng(lat_lng)

            return points_to_edge[tuple(found_point)]
        # catch value errors if not enough points were given
        except ValueError:
            logging.error("No edge found. Using fallback calculation.")
            return self.find_closest_edge_by_lat_lng(lat_lng)
