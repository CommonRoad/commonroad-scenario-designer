"""
GraphEdge class
"""

import math
from typing import List, Optional, Set, Tuple

import numpy as np
from ordered_set import OrderedSet

from crdesigner.common.config.osm_config import osm_config as config
from crdesigner.map_conversion.common import geometry
from crdesigner.map_conversion.osm2cr.converter_modules.utility.custom_types import (
    Assumption_info,
    Road_info,
)

from ._graph_lane import Lane
from ._graph_node import GraphNode
from ._graph_traffic_light import GraphTrafficLight
from ._graph_traffic_sign import GraphTrafficSign


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
        :param node1: node the edge starts at
        :param node2: node the edge ends at
        :param waypoints: list of waypoints for the course of the edge
        :param lane_info: information about lanes on the edge
        :param assumptions: assumptions made about the edge
        :param speedlimit: speed limit on the edge
        :param roadtype: type of road the edge represents
        """
        (
            nr_of_lanes,
            forward_lanes,
            backward_lanes,
            oneway,
            turnlanes,
            turnlanes_forward,
            turnlanes_backward,
        ) = lane_info
        lane_nr_assumed, lanes_assumed, oneway_assumed = assumptions
        self.id: int = id
        self.node1: GraphNode = node1
        self.node2: GraphNode = node2
        self.waypoints: List[geometry.Point] = waypoints
        self.nr_of_lanes: int = nr_of_lanes
        # number of forward lanes
        self.forward_lanes: int = forward_lanes
        # number of backward lanes
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
        return "Graph_edge {}: {}->{}".format(self.id, self.node1.id, self.node2.id)

    def __repr__(self):
        return "Graph_edge {}: {}->{}".format(self.id, self.node1.id, self.node2.id)

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
            raise ValueError("this edge has not enough waypoints to determine its orientation")
        if node == self.node1:
            x = self.waypoints[1].x - self.waypoints[0].x
            y = self.waypoints[1].y - self.waypoints[0].y
        elif node == self.node2:
            x = self.waypoints[-2].x - self.waypoints[-1].x
            y = self.waypoints[-2].y - self.waypoints[-1].y
        else:
            raise ValueError("the given node is not an endpoint of this edge")
        return np.arctan2(y, x) + np.pi

    def get_compass_degrees(self):
        """
        calculates the compass degrees of an edge as in
        https://en.wikipedia.org/wiki/Points_of_the_compass#/media/File:Compass_Card_B+W.svg
        :return: compass orientation in degrees
        """

        # compute radians
        delta_x = self.node2.x - self.node1.x
        delta_y = self.node2.y - self.node1.y
        radians = np.arctan2(delta_y, delta_x)

        # https://stackoverflow.com/a/7805311
        if radians < 0.0:
            radians = abs(radians)
        else:
            radians = 2 * np.pi - radians
        degrees = math.degrees(radians)
        degrees += 90.0
        if degrees > 360.0:
            degrees -= 360.0
        # return correctly computed degrees
        return degrees

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
                    p3 = geometry.get_inner_bezier_point(self.waypoints[2].get_array(), p4, p1, d)
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
            while index >= 0 and np.linalg.norm(waypoints[index] - point) < distance:
                index -= 1
            return 0, index
        else:
            index = 0
            while index < len(waypoints) and np.linalg.norm(waypoints[index] - point) < distance:
                index += 1
            return index, len(waypoints) - 1

    def crop(self, index1: int, index2: int, edges_to_delete: List["GraphEdge"]) -> None:
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

    def add_traffic_sign(self, sign: GraphTrafficSign):
        """
        adds traffic signs to all lanes of the edge

        :param sign: the sign to add

        :return: None
        """

        # TODO handle direction for traffic signs where no direction is given (e.g parsed maxspeed from OSM).
        # Currently, every sign of these is added to the forward lane only

        self.traffic_signs.append(sign)
        forward = True
        sign_direction = sign.direction
        # add traffic sign to direction wise lane if direction is given.
        # This is the case for all mapillary signs
        if sign_direction is not None:
            # get compass degrees of edge
            edge_orientation = self.get_compass_degrees()
            if abs(sign_direction - edge_orientation) < 180:
                forward = False
        for lane in self.lanes:
            # add sign to forward lanes
            if lane.forward and forward:
                lane.add_traffic_sign(sign)
            # add to backward lanes
            elif (not lane.forward) and (not forward):
                lane.add_traffic_sign(sign)

    def add_traffic_light(self, light: GraphTrafficLight, forward):
        """
        adds traffic light to all lanes of the edge

        :param light: the light to add

        :return: None
        """

        self.traffic_lights.append(light)
        for lane in self.lanes:
            if lane.forward == forward:
                lane.add_traffic_light(light)
