"""
This module holds the classes required for the graph structure.
It also provides several methods to perform operations on elements of the graph.
"""
from queue import Queue
from typing import List, Set, Tuple, Optional, Dict
from ordered_set import OrderedSet
import numpy as np
from commonroad.scenario.traffic_sign import TrafficSignElement, TrafficSign, TrafficLight, TrafficSignIDGermany
from commonroad.geometry.shape import Polygon

from crmapconverter.osm2cr import config
from crmapconverter.osm2cr.converter_modules.utility import geometry, idgenerator
from crmapconverter.osm2cr.converter_modules.utility.custom_types import (
    Road_info,
    Assumption_info,
)


def graph_search(center_node: "GraphNode") -> Tuple[Set["GraphNode"], Set["GraphEdge"]]:
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


def find_adjacents(newlane: "Lane", lanes: Set["Lane"]) -> Set["Lane"]:
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


def sort_adjacent_lanes(lane: "Lane") -> Tuple[List["Lane"], List[bool]]:
    """
    sorts the adjacent lanes as they are in edges

    :param lanes: the lanes to sort
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


def set_points(predecessor: "Lane", successor: "Lane") -> List[np.ndarray]:
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
        # print("found something")
        pass
    if (
        a1 > 0
        and a2 > 0
        and (distance_to_points > 1 or distance_to_points / total_distance > 0.1)
    ):
        waypoints = geometry.evaluate_bezier(np.array([p1, intersection_point, p4]), n)
        waypoints.append(p4)
    # else use cubic bezier
    else:
        waypoints = geometry.evaluate_bezier(np.array([p1, p2, p3, p4]), n)
        waypoints.append(p4)
    return waypoints


class GraphNode:
    """
    Class that represents a node in the graph

    """

    def __init__(self, id: int, x: float, y: float, edges: Set["GraphEdge"]):
        """
        creates a graph node

        :param id: unique id of the node
        :param x: x coordinate
        :param y: y coordinate
        :param edges:  set of edges connected to the node
        """
        self.id = id
        self.x = x
        self.y = y
        self.edges = edges
        self.traffic_signs = []
        self.traffic_lights = []
        self.is_crossing = False

    def __str__(self):
        return "Graph_node with id: {}".format(self.id)

    def __repr__(self):
        return "Graph_node with id: {}".format(self.id)

    def get_degree(self) -> int:
        """
        gets the degree of the node

        :return: degree of node
        """
        return len(self.edges)

    def get_cooridnates(self) -> np.ndarray:
        """
        gets coordinates as numpy array

        :return: coordinates in numpy array
        """
        return np.array([self.x, self.y])

    def get_point(self) -> geometry.Point:
        """
        gets a Point object which is located at the node

        :return: a Point object located at the node
        """
        return geometry.Point(None, self.x, self.y)

    def get_distance(self, other: "GraphNode") -> float:
        """
        calculates distance to other node

        :param other: other node
        :return: distance between nodes
        """
        return np.linalg.norm(self.get_cooridnates() - other.get_cooridnates())

    def get_highest_edge_distance(self) -> float:
        """
        gets the highest distance a connected edge has to the node

        :return: highest distance to connected edge
        """
        result = 0.0
        for edge in self.edges:
            if edge.node1 == self:
                distance = np.linalg.norm(
                    edge.get_interpolated_waypoints()[0] - self.get_cooridnates()
                )
            elif edge.node2 == self:
                distance = np.linalg.norm(
                    edge.get_interpolated_waypoints()[-1] - self.get_cooridnates()
                )
            else:
                raise ValueError("Graph is malformed")
            result = max(result, distance)
        return result

    def get_neighbors(self) -> Set["GraphNode"]:
        """
        finds nodes which are connected to this node via a single edge

        :return: set of neighbors
        """
        res = set()
        for edge in self.edges:
            res |= {edge.node1, edge.node2}
        res.discard(self)
        return res

    def set_coordinates(self, position: np.ndarray) -> None:
        """
        sets the coordinates of a node to the position given in a numpy array

        :param position: new position
        :return: None
        """
        self.x = position[0]
        self.y = position[1]

    def move_to(self, position: np.ndarray) -> None:
        """
        moves a node in the graph, also moves the waypoints of all edges which start or end at the node
        WARNING! this method should only be used before the course of the lanes in the graph are generated

        :param position: new position
        :return: None
        """
        self.set_coordinates(position)
        for edge in self.edges:
            if edge.node1 == self:
                edge.waypoints[0].set_position(position)
            elif edge.node2 == self:
                edge.waypoints[-1].set_position(position)
            else:
                raise ValueError(
                    "malformed graph, node has edges assigned to it, which start elsewhere"
                )

    def add_traffic_sign(self, sign: "GraphTrafficSign"):
        self.traffic_signs.append(sign)
        # add to lanes
        for edge in self.edges:
            for lane in edge.lanes:
                # add to forward lanes
                # TODO determine in which direction
                if lane.forward:
                    lane.add_traffic_sign(sign)


class GraphEdge:
    """
    Class that represents an edge in the graph structure

    """

    def __init__(
        self,
        id: int,
        node1: GraphNode,
        node2: GraphNode,
        waypoints: List[geometry.Point],
        lane_info: Road_info,
        assumptions: Assumption_info,
        speedlimit: float,
        roadtype: str,
    ):
        """
        creates an edge

        :param id: unique id
        :type id: int
        :param node1: node the edge starts at
        :type node1: GraphNode
        :param node2: node the edge ends at
        :type node2: GraphNode
        :param waypoints: list of waypoints for the course of the edge
        :type waypoints: List[geometry.Point]
        :param lane_info: information about lanes on the edge
        :type lane_info: Road_info
        :param assumptions: assumptions made about the edge
        :type assumptions: Assumption_info
        :param speedlimit: speed limit on the edge
        :type speedlimit: float
        :param roadtype: type of road the edge represents
        :type roadtype: str
        """
        nr_of_lanes, forward_lanes, backward_lanes, oneway, turnlanes, turnlanes_forward, turnlanes_backward = (
            lane_info
        )
        lane_nr_assumed, lanes_assumed, oneway_assumed = assumptions
        self.id: int = id
        self.node1: GraphNode = node1
        self.node2: GraphNode = node2
        self.waypoints: List[geometry.Point] = waypoints
        self.nr_of_lanes: int = nr_of_lanes
        self.forward_lanes: int = forward_lanes
        self.backward_lanes: int = backward_lanes
        self.oneway: bool = oneway
        self.speedlimit: float = speedlimit
        self.roadtype: str = roadtype
        self.turnlanes_forward: Optional[List[str]] = turnlanes_forward
        self.turnlanes_backward: Optional[List[str]] = turnlanes_backward
        self.lane_nr_assumed: bool = lane_nr_assumed
        self.lanes_assumed: bool = lanes_assumed
        self.oneway_assumed: bool = oneway_assumed
        self.lanes: List[Lane] = []
        self.interpolated_waypoints: Optional[List[np.ndarray]] = None
        self.central_points: Optional[Tuple[int, int]] = None
        self.forward_successor: Optional[GraphEdge] = None
        self.backward_successor: Optional[GraphEdge] = None
        self.lanewidth: float = config.LANEWIDTHS[roadtype]
        self.forward_restrictions: Set[str] = set()
        self.backward_restrictions: Set[str] = set()
        self.traffic_signs = []
        self.traffic_lights = []

    def __str__(self):
        return "Graph_edge {}: {}->{}".format(
            self.id,self.node1.id,self.node2.id)

    def __repr__(self):
        return "Graph_edge {}: {}->{}".format(
            self.id,self.node1.id,self.node2.id)

    def flip(self) -> None:
        """
        flips the direction of the edge and all its lanes
        this can be used if nr of forward lanes was changed to zero
        only use this if edge has >=1 backward lanes at start

        :return: None
        """
        assert self.backward_lanes > 0 or self.oneway
        if self.oneway:
            # flip behaves differently for oneway streets
            self.node1, self.node2 = self.node2, self.node1
            for lane in self.lanes:
                lane.flip(True)
            self.lanes = self.lanes[::-1]
            if self.waypoints is not None:
                self.waypoints = self.waypoints[::-1]
            if self.interpolated_waypoints is not None:
                self.interpolated_waypoints = self.interpolated_waypoints[::-1]
            self.forward_successor, self.backward_successor = (
                self.backward_successor,
                self.forward_successor,
            )
            self.forward_restrictions = set()
            self.backward_restrictions = set()
            self.turnlanes_forward = None
            self.turnlanes_backward = None
        else:
            self.node1, self.node2 = self.node2, self.node1
            for lane in self.lanes:
                lane.flip(False)
            self.lanes = self.lanes[::-1]
            if self.waypoints is not None:
                self.waypoints = self.waypoints[::-1]
            if self.interpolated_waypoints is not None:
                self.interpolated_waypoints = self.interpolated_waypoints[::-1]
            self.forward_successor, self.backward_successor = (
                self.backward_successor,
                self.forward_successor,
            )
            self.forward_restrictions, self.backward_restrictions = (
                self.backward_restrictions,
                self.forward_restrictions,
            )
            self.forward_lanes, self.backward_lanes = (
                self.backward_lanes,
                self.forward_lanes,
            )
            self.turnlanes_forward, self.turnlanes_backward = (
                self.turnlanes_backward,
                self.turnlanes_forward,
            )
        assert self.forward_lanes > 0

    def points_to(self, node: GraphNode) -> bool:
        """
        determines if edge ends at node

        :param node: checked node
        :return: True if edge ends at node, else False
        """
        return node == self.node2

    def get_orientation(self, node: GraphNode) -> float:
        """
        calculates the orientation of an edge at a specified end

        :param node: node at whose end the orientation is calculated
        :return: orientation in radians
        """
        if len(self.waypoints) < 2:
            raise ValueError(
                "this edge has not enough waypoints to determine its orientation"
            )
        if node == self.node1:
            x = self.waypoints[1].x - self.waypoints[0].x
            y = self.waypoints[1].y - self.waypoints[0].y
        elif node == self.node2:
            x = self.waypoints[-2].x - self.waypoints[-1].x
            y = self.waypoints[-2].y - self.waypoints[-1].y
        else:
            raise ValueError("the given node is not an endpoint of this edge")
        return np.arctan2(y, x) + np.pi

    def angle_to(self, edge: "GraphEdge", node: GraphNode) -> float:
        """
        calculates the angle between two edges at a given node in radians

        :param edge: the other edge
        :param node: the node at which the angle is calculated
        :return: the angle between the edges
        """
        diff1 = abs(self.get_orientation(node) - edge.get_orientation(node))
        diff2 = np.pi * 2 - diff1
        return min(diff1, diff2)

    def soft_angle(self, edge: "GraphEdge", node: GraphNode) -> bool:
        """
        determines if the angle to another edge is soft

        :param edge: other edge
        :param node: the node at which the ange is calculated
        :return: True if angle is soft, else False
        """
        threshold = np.deg2rad(config.SOFT_ANGLE_THRESHOLD)
        return self.angle_to(edge, node) > threshold

    def get_width(self) -> float:
        """
        calculates the width of the road the edge represents

        :return: width
        """
        return self.nr_of_lanes * config.LANEWIDTHS[self.roadtype]

    def generate_lanes(self) -> None:
        """
        generates lanes for the edge

        :return: None
        """
        assert self.forward_lanes + self.backward_lanes == self.nr_of_lanes
        backwardlanes = []
        for count in range(self.backward_lanes):
            turnlane = "none"
            if self.turnlanes_backward is not None:
                turnlane = self.turnlanes_backward[-(count + 1)]
            new_lane = Lane(
                self,
                OrderedSet(),
                OrderedSet(),
                turnlane,
                self.lanewidth,
                self.lanewidth,
                self.node2,
                self.node1,
                self.speedlimit,
            )
            new_lane.forward = False
            backwardlanes.append(new_lane)
        forwardlanes = []
        for count in range(self.forward_lanes):
            turnlane = "none"
            if self.turnlanes_forward is not None:
                turnlane = self.turnlanes_forward[count]
            new_lane = Lane(
                self,
                OrderedSet(),
                OrderedSet(),
                turnlane,
                self.lanewidth,
                self.lanewidth,
                self.node1,
                self.node2,
                self.speedlimit,
            )
            new_lane.forward = True
            forwardlanes.append(new_lane)

        for index, lane in enumerate(backwardlanes[:-1]):
            lane.adjacent_left = backwardlanes[index + 1]
            lane.adjacent_left_direction_equal = True
            backwardlanes[index + 1].adjacent_right = lane
            backwardlanes[index + 1].adjacent_right_direction_equal = True
        for index, lane in enumerate(forwardlanes[:-1]):
            lane.adjacent_right = forwardlanes[index + 1]
            lane.adjacent_right_direction_equal = True
            forwardlanes[index + 1].adjacent_left = lane
            forwardlanes[index + 1].adjacent_left_direction_equal = True
        if len(forwardlanes) > 0 and len(backwardlanes) > 0:
            backwardlanes[-1].adjacent_left = forwardlanes[0]
            backwardlanes[-1].adjacent_left_direction_equal = False
            forwardlanes[0].adjacent_left = backwardlanes[-1]
            forwardlanes[0].adjacent_left_direction_equal = False

        self.lanes = backwardlanes + forwardlanes
        assert len(self.lanes) == self.nr_of_lanes

    def get_interpolated_waypoints(self, save=True) -> List[np.ndarray]:
        """
        loads the interpolated waypoints if already generated
        interpolates waypoints, otherwise

        :param save: set to true if the edge should save the waypoints, default is true
        :return: interpolated waypoints
        """
        if self.interpolated_waypoints is not None:
            return self.interpolated_waypoints
        else:
            point_distance = config.INTERPOLATION_DISTANCE_INTERNAL
            d = config.BEZIER_PARAMETER
            result = []
            if len(self.waypoints) <= 2:
                p1 = self.waypoints[0].get_array()
                p2 = self.waypoints[1].get_array()
                n = max(int(np.linalg.norm(p1 - p2) / point_distance), 2)
                for index in range(n):
                    result.append(p1 + (p2 - p1) * index / n)
                result.append(p2)
                if save:
                    self.interpolated_waypoints = result
                    self.central_points = (int(len(result) / 2 - 1), int(len(result) / 2))
                return result
            for index in range(len(self.waypoints) - 1):
                if index == 0:
                    p1, p4 = (
                        self.waypoints[0].get_array(),
                        self.waypoints[1].get_array(),
                    )
                    p2 = p1 + (p4 - p1) * d
                    p3 = geometry.get_inner_bezier_point(
                        self.waypoints[2].get_array(), p4, p1, d
                    )
                elif index == len(self.waypoints) - 2:
                    p1, p4 = (
                        self.waypoints[index].get_array(),
                        self.waypoints[index + 1].get_array(),
                    )
                    p2 = geometry.get_inner_bezier_point(
                        self.waypoints[index - 1].get_array(), p1, p4, d
                    )
                    p3 = p4 + (p1 - p4) * d
                else:
                    segment_points = []
                    for i in range(4):
                        segment_points.append(self.waypoints[index + i - 1])
                    segment_points = [x.get_array() for x in segment_points]
                    p1, p2, p3, p4 = geometry.get_bezier_points_of_segment(
                        np.array(segment_points), d
                    )
                n = max(int(np.linalg.norm(p1 - p4) / point_distance), 2)
                result += geometry.evaluate_bezier(np.array([p1, p2, p3, p4]), n)
            if save:
                self.interpolated_waypoints = result
                self.central_points = (int(len(result) / 2 - 1), int(len(result) / 2))
            return result

    def get_crop_index(self, node: GraphNode, distance: float) -> Tuple[int, int]:
        """
        calculates the index to which the edge needs to be cropped to have a specified distance to a node

        :param node: the node, the distance refers to
        :param distance: the desired distance to the node
        :return: index of new start and end of waypoints
        """
        point = np.array([node.x, node.y])
        waypoints = self.get_interpolated_waypoints()
        if self.node2 == node:
            index = len(waypoints) - 1
            while (index >= 0 and np.linalg.norm(waypoints[index] - point) < distance):
                index -= 1
            return 0, index
        else:
            index = 0
            while (
                index < len(waypoints)
                and np.linalg.norm(waypoints[index] - point) < distance
            ):
                index += 1
            return index, len(waypoints) - 1

    def crop(
        self, index1: int, index2: int, edges_to_delete: List["GraphEdge"]
    ) -> None:
        """
        crops waypoints of edge to given indices
        if remaining interval is empty, it is set to the center two elements
        also the edge is added to the list of edges that will be deleted


        :param index1: index of first waypoint included
        :param index2: index of first waypoint excluded
        :param edges_to_delete: list of edges that will be deleted
        :return: None
        """
        waypoints = self.get_interpolated_waypoints()
        assert index1 in range(len(waypoints))
        assert index2 in range(len(waypoints))
        if index1 >= index2 - 1:
            if self not in edges_to_delete:
                edges_to_delete.append(self)
            middle = int((index1 + index2) / 2)
            index1 = max(0, middle - 1)
            index2 = index1 + 2
            assert index1 in range(len(waypoints))
            assert index2 in range(len(waypoints) + 1)
        self.interpolated_waypoints = waypoints[index1:index2]

    def exchange_node(self, node_old: GraphNode, node_new: GraphNode) -> None:
        """
        Exchanges a node of an edge with a new node

        :param node_old: Node to be replaced
        :param node_new: Node to replace with
        :return: None
        """
        if node_old == self.node1:
            self.node1 = node_new
        elif node_old == self.node2:
            self.node2 = node_new
        else:
            raise ValueError("node_old is not assigned to Edge")
        for lane in self.lanes:
            lane.exchange_node(node_old, node_new)
        return

    def common_node(self, other_edge: "GraphEdge") -> Optional[GraphNode]:
        """
        finds the common node between two edges

        :param other_edge:
        :return: the common node, None if there is no common node
        """
        if other_edge.node1 == self.node1 or other_edge.node2 == self.node1:
            return self.node1
        elif other_edge.node1 == self.node2 or other_edge.node2 == self.node2:
            return self.node2

    def get_waypoints(self) -> np.ndarray:
        """
        returns the waypoints as a numpy array

        :return: waypoints as np array
        """
        return np.array([p.get_array() for p in self.waypoints])

    def add_traffic_sign(self, sign: "GraphTrafficSign"):
        self.traffic_signs.append(sign)
        # add to lanes
        for lane in self.lanes:
            # add to forward lanes
            if lane.forward:
                lane.add_traffic_sign(sign)

    def add_traffic_light(self, light: "GraphTrafficLight", forward):
        self.traffic_lights.append(light)
        for lane in self.lanes:
            if lane.forward == forward:
                lane.add_traffic_light(light)


class GraphTrafficSign:
    def __init__(self, sign: Dict,
                 node: GraphNode = None, edges: List = []):
        self.sign = sign
        self.node = node
        self.edges = edges
        self.id = idgenerator.get_id()

    def to_traffic_sign_cr(self):
        elements = []
        position = None
        values = []

        # map OSM sign to country sign
        # TODO Currently only Germany supported. Add more locations.
        traffic_sign_map = {
            'maxspeed': TrafficSignIDGermany.MAX_SPEED,
            'overtaking': TrafficSignIDGermany.NO_OVERTAKING_START,
            'city_limit': TrafficSignIDGermany.TOWN_SIGN,
            'give_way': TrafficSignIDGermany.YIELD,
            'stop': TrafficSignIDGermany.STOP,
            '260': TrafficSignIDGermany.BAN_CAR_TRUCK_BUS_MOTORCYCLE,
            'unknown': TrafficSignIDGermany.UNKNOWN
        }

        # get position
        if self.node is not None:
            position_point = self.node.get_cooridnates()

        # extract traffic sign values
        # maxspeed
        if 'maxspeed' in self.sign:
            sign_id = traffic_sign_map['maxspeed']
            value = self.sign['maxspeed']
            elements.append(TrafficSignElement(sign_id, [value]))

        # if traffic sign
        elif 'traffic_sign' in self.sign:
            key = self.sign['traffic_sign']

            # speed limit
            if 'DE:274' in str(key):
                sign_id = traffic_sign_map['maxspeed']
                max_speed = float(key[key.find("[") + 1:key.find("]")])
                # convert km/h to m/s
                max_speed /= 3.6
                elements.append(TrafficSignElement(sign_id, [max_speed]))

            # regular traffic sign
            else:
                found_sign = False
                for traffic_sign in traffic_sign_map:
                    if traffic_sign in str(key):
                        sign_id = traffic_sign_map[traffic_sign]
                        value = ' '  # TODO add specific values for some traffic signs
                        elements.append(TrafficSignElement(sign_id, [value]))
                        found_sign = True
                        break

                # unknown traffic sign
                if not found_sign:
                    sign_id = traffic_sign_map['unknown']
                    value = 'unknown sign'
                    elements.append(TrafficSignElement(sign_id, [value]))

        # determine if virtual
        virtual = False
        if 'virtual' in self.sign:
            if not self.sign['virtual']:
                virtual = False
            else:
                virtual = self.sign['virtual']

        # TODO Maybe improve this
        first_occurrence = set()

        return TrafficSign(
            traffic_sign_id=self.id,
            traffic_sign_elements=elements,
            first_occurrence=first_occurrence,
            position=position,
            virtual=virtual)


class GraphTrafficLight:
    def __init__(self, light: Dict,
                 node: GraphNode):
        self.light = light
        self.node = node
        self.id = idgenerator.get_id()
        self.crossing = False
        self.highway = False
        self.forward = True
        self.parse_osm(light)

    def parse_osm(self, data: Dict):
        if 'crossing' in data:
            self.crossing = True
        if 'highway' in data:
            self.highway = True
        if 'traffic_signals:direction' in data:
            if data['traffic_signals:direction'] == 'backward':
                self.forward = False

    def to_traffic_light_cr(self):
        position = None
        if self.node is not None:
            position_point = self.node.get_point()
            position = np.array([position_point.x, position_point.y])
        traffic_light = TrafficLight(self.id, cycle=[], position=position)
        return traffic_light


class Lane:
    """
    Class that represents a lane in the graph structure

    """

    def __init__(
        self,
        edge: Optional[GraphEdge],
        successors: Set["Lane"],
        predecessors: Set["Lane"],
        turnlane: str,
        width1: float,
        width2: float,
        from_node: GraphNode,
        to_node: GraphNode,
        speedlimit: float,
    ):
        """
        creates a lane

        :param edge: the edge the lane belongs to
        :param successors: Set of successors of the lane
        :param predecessors: Set of predecessors of the lane
        :param turnlane: turn lane tag of the lane
        :param width1: width of the lane at the start
        :param width2: width of the lane at the end
        :param from_node: node the lane starts at
        :param to_node: node the lane ends at
        :param speedlimit: speed limit on the lane
        """
        self.edge = edge
        self.successors = successors
        self.predecessors = predecessors
        self.forward: Optional[bool] = None
        self.waypoints: Optional[List[np.ndarray]] = None
        self.turnlane = turnlane
        self.adjacent_left: Optional[Lane] = None
        self.adjacent_right: Optional[Lane] = None
        self.id = idgenerator.get_id()
        self.left_bound: Optional[List[np.ndarray]] = None
        self.right_bound: Optional[List[np.ndarray]] = None
        self.width1 = width1
        self.width2 = width2
        self.from_node = from_node
        self.to_node = to_node
        self.adjacent_left_direction_equal: Optional[bool] = None
        self.adjacent_right_direction_equal: Optional[bool] = None
        self.speedlimit = speedlimit
        self.traffic_signs = None
        self.traffic_lights = None

    def __str__(self):
        return "Lane with id: {}".format(self.id)

    def __repr__(self):
        return "Lane with id: {}".format(self.id)

    def flip(self, keep_edge_dir: bool) -> None:
        """
        flips the direction of the lane
        this method is only used by GraphEdge.flip()

        :param keep_edge_dir: if true, self.forward will not be inverted
        :return: None
        """
        assert self.successors is None or len(self.successors) == 0
        assert self.predecessors is None or len(self.predecessors) == 0
        assert self.left_bound is None
        assert self.right_bound is None

        if self.waypoints is not None:
            self.waypoints = self.waypoints[::-1]
        self.width1, self.width2 = self.width2, self.width1
        self.from_node, self.to_node = self.to_node, self.from_node
        if self.forward is not None and not keep_edge_dir:
            self.forward = not self.forward

    def intersects(self, other: "Lane") -> bool:
        """
        checks if lane intersects with another lane

        :param other: the other lane
        :return: True if lanes intersect, else False
        """
        result = bool(self.successors & other.successors) or bool(
            self.predecessors & other.predecessors
        )
        return result

    def get_node(self, start: bool) -> GraphNode:
        """
        returns the node of a lane
        if the lane is assigned to an edge it returns its first or second node
        otherwise it returns the node it leads to or from

        :param start: true if the first node is desired, false for the second node
        :return: the node
        """
        if self.edge is not None:
            if self.forward == start:
                return self.edge.node1
            else:
                return self.edge.node2
        else:
            if start:
                return next(iter(self.predecessors)).get_node(False)
            else:
                return next(iter(self.successors)).get_node(True)

    def create_bounds(self) -> None:
        """
        creates the bounds of a lane

        :return: None
        """
        n = len(self.waypoints)
        left_bound = None
        if self.adjacent_left is not None and not self.intersects(self.adjacent_left):
            assert self.adjacent_left_direction_equal is not None
            if self.adjacent_left_direction_equal:
                left_bound = self.adjacent_left.right_bound
            elif self.adjacent_left.left_bound is not None:
                left_bound = self.adjacent_left.left_bound[::-1]
            if left_bound is not None and len(left_bound) != n:
                # do not copy bounds of faulty length
                left_bound = None
        if left_bound is None:
            left_bound, _ = geometry.create_tilted_parallels(
                self.waypoints, self.width1 / 2, self.width2 / 2
            )
        right_bound = None
        if self.adjacent_right is not None and not self.intersects(self.adjacent_right):
            assert self.adjacent_right_direction_equal is not None
            if self.adjacent_right_direction_equal:
                right_bound = self.adjacent_right.left_bound
            elif self.adjacent_right.right_bound is not None:
                right_bound = self.adjacent_right.right_bound[::-1]
            if right_bound is not None and len(right_bound) != n:
                # do not copy bounds of faulty length
                right_bound = None
        if right_bound is None:
            _, right_bound = geometry.create_tilted_parallels(
                self.waypoints, self.width1 / 2, self.width2 / 2
            )
        assert left_bound is not None
        assert right_bound is not None
        self.left_bound = left_bound
        self.right_bound = right_bound
        return

    def set_nr_of_way_points(self, n: int) -> None:
        """
        sets the number of waypoints to n

        :param n: the new number of waypoints
        :return: None
        """
        n = max(2, n)
        self.waypoints = geometry.set_line_points(self.waypoints, n)

    def get_point(self, position: str) -> np.ndarray:
        """
        gets the waypoint representing a corner of a lane

        :param position: a string defining the corner
        :return: the corresponding waypoint
        """
        if position == "startleft":
            return self.left_bound[0]
        elif position == "startright":
            return self.right_bound[0]
        elif position == "endleft":
            return self.left_bound[-1]
        elif position == "endright":
            return self.right_bound[-1]
        else:
            raise ValueError("invalid Position")

    def set_point(self, position: str, point: np.ndarray) -> None:
        """
        sets the waypoint representing a corner of a lane

        :param position: a string defining the corner
        :param point: newcoordinates of point
        :return: None
        """
        if position == "startleft":
            self.left_bound[0] = point
        elif position == "startright":
            self.right_bound[0] = point
        elif position == "endleft":
            self.left_bound[-1] = point
        elif position == "endright":
            self.right_bound[-1] = point
        else:
            raise ValueError("invalid Position")

    def exchange_node(self, node_old, node_new) -> None:
        """
        exchanges an old node with a new node, if lane starts or ends at node

        :param node_old: the node to replace
        :param node_new: the new node
        :return: None
        """
        if node_old == self.from_node:
            self.from_node = node_new
        elif node_old == self.to_node:
            self.to_node = node_new
        else:
            raise ValueError("node is not assigned to this edge")
        return

    def convert_to_polygon(self) -> Polygon:
        """
        Converts the given lanelet to a polygon representation

        :return: The polygon of the lanelet
        """
        if (not self.right_bound) or (not self.left_bound):
            self.create_bounds()
        assert self.right_bound is not None
        assert self.left_bound is not None

        polygon = Polygon(np.concatenate((self.right_bound, np.flip(self.left_bound, 0))))
        return polygon

    def add_traffic_sign(self, sign: GraphTrafficSign):
        if self.traffic_signs is None:
            self.traffic_signs = []
        self.traffic_signs.append(sign)

    def add_traffic_light(self, light: GraphTrafficLight):
        if self.traffic_lights is None:
            self.traffic_lights = []
        self.traffic_lights.append(light)


class Graph:
    def __init__(
        self,
        nodes: Set[GraphNode],
        edges: Set[GraphEdge],
        center_point: Tuple[float, float],
        bounds: Tuple[float, float, float, float],
        traffic_signs: List[GraphTrafficSign],
        traffic_lights: List[GraphTrafficLight]
    ) -> None:
        """
        creates a new graph

        :param nodes: nodes of the graph
        :param edges: edges of the graph
        :param center_point: gps coordinates of the origin
        :return: None
        """
        self.nodes = nodes
        self.edges = edges
        self.lanelinks: Set[Lane] = OrderedSet()
        self.center_point = center_point
        self.bounds = bounds
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
                    other_edges = edges[:index] + edges[index + 1:]
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
                cropping_dist = intersection_dist/10.0
            else:
                cropping_dist = intersection_dist
            node_point = np.array([node.x, node.y])
            node_edges = list(node.edges)
            for index, edge in enumerate(node_edges):
                distance = 0
                edgewaypoints = edge.get_interpolated_waypoints()
                if edge.points_to(node):
                    edgewaypoints = edgewaypoints[::-1]
                other_edges = node_edges[index + 1:] + node_edges[:index]
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
                                edge.get_width() / 2
                                + other_edge.get_width() / 2
                                + cropping_dist
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
                        distance = max(
                            distance, np.linalg.norm(edgewaypoints[i] - node_point)
                        )
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
                update_forward(
                    lane.adjacent_right, lane.adjacent_right_direction_equal == forward
                )
            if lane.adjacent_left is not None and lane.adjacent_left.forward is None:
                update_forward(
                    lane.adjacent_left, lane.adjacent_left_direction_equal == forward
                )
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
            print("filtering points")
            for edge in self.edges:
                lines = [
                    lane.waypoints if lane.forward else lane.waypoints[::-1]
                    for lane in edge.lanes
                ]
                lines = geometry.pre_filter_points(lines)
                lines = geometry.filter_points(lines, config.COMPRESSION_THRESHOLD)
                for index, lane in enumerate(edge.lanes):
                    lane.waypoints = (
                        lines[index] if lane.forward else lines[index][::-1]
                    )
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
                    lane.waypoints = (
                        lines[index] if forward[index] else lines[index][::-1]
                    )

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
                    sub_edge.add_traffic_sign(sign)

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
        if lane in self.lanelinks:
            self.lanelinks.remove(lane)
        for edge in self.edges:
            if lane in edge.lanes:
                edge.lanes.remove(lane)

    def delete_invalid_lanes(self) -> None:
        """
        finds and deletes invalid lanes in the RoadGraph

        :return: None
        """
        invalid_lanes = self.find_invalid_lanes()
        for lane in invalid_lanes:
            self.delete_lane(lane)
        self.set_adjacents()

class SublayeredGraph(Graph):

    def __init__(
        self,
        nodes: Set[GraphNode],
        edges: Set[GraphEdge],
        center_point: Tuple[float, float],
        bounds: Tuple[float, float, float, float],
        traffic_signs: List[GraphTrafficSign],
        traffic_lights: List[GraphTrafficLight],
        sublayer_graph: Graph
    ):
        super().__init__(
            nodes, edges, center_point, bounds, traffic_signs, traffic_lights
        )
        # graph that is connected by crossings only (e.g. pedestrian path)
        self.sublayer_graph = sublayer_graph
        self.apply_on_sublayer = True

    def make_contiguous(self) -> None:
        # TODO respective crossing nodes
        super().make_contiguous()
        if self.apply_on_sublayer:
            self.sublayer_graph.make_contiguous()

    def link_edges(self) -> None:
        super().link_edges()
        if self.apply_on_sublayer:
            self.sublayer_graph.link_edges()

    def create_lane_waypoints(self) -> None:
        super().create_lane_waypoints()
        if self.apply_on_sublayer:
            self.sublayer_graph.create_lane_waypoints()

    def interpolate(self) -> None:
        super().interpolate()
        if self.apply_on_sublayer:
            self.sublayer_graph.interpolate()

    def create_lane_link_segments(self) -> None:
        super().create_lane_link_segments()
        if self.apply_on_sublayer:
            self.sublayer_graph.create_lane_link_segments()

    def create_lane_bounds(
            self, interpolation_scale: Optional[float] = None) -> None:
        super().create_lane_bounds(interpolation_scale)
        if self.apply_on_sublayer:
            self.sublayer_graph.create_lane_bounds(interpolation_scale)

    def correct_start_end_points(self) -> None:
        super().correct_start_end_points()
        if self.apply_on_sublayer:
            self.sublayer_graph.correct_start_end_points()

    def apply_traffic_signs(self) -> None:
        super().apply_traffic_signs()
        if self.apply_on_sublayer:
            self.sublayer_graph.apply_traffic_signs()

    def apply_traffic_lights(self) -> None:
        super().apply_traffic_lights()
        if self.apply_on_sublayer:
            self.sublayer_graph.apply_traffic_lights()

    def delete_invalid_lanes(self) -> None:
        super().delete_invalid_lanes()
        if self.apply_on_sublayer:
            self.sublayer_graph.delete_invalid_lanes()
