from __future__ import annotations

import math
from typing import TYPE_CHECKING, List, Optional, Set

import numpy as np
from commonroad.geometry.shape import Polygon

from crdesigner.map_conversion.common import geometry
from crdesigner.map_conversion.osm2cr.converter_modules.utility import idgenerator

from ._graph_node import GraphNode
from ._graph_traffic_light import GraphTrafficLight
from ._graph_traffic_sign import GraphTrafficSign

if TYPE_CHECKING:
    from ._graph_edge import GraphEdge


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

    def get_compass_degrees(self):
        """
        calculates the compass degrees of a lane as in
        https://en.wikipedia.org/wiki/Points_of_the_compass#/media/File:Compass_Card_B+W.svg
        :return: compass orientation in degrees
        """

        def get_orientation():
            # since self.waypoints is not always available, self.from_node and self.to_node are used instead.
            x = self.from_node.x - self.to_node.x
            y = self.from_node.y - self.to_node.y
            return np.arctan2(y, x) + np.pi

        lane_compass_degrees = math.degrees(get_orientation()) - 45
        if lane_compass_degrees < 0.0:
            lane_compass_degrees += 360.0
        return lane_compass_degrees

    def add_traffic_sign(self, sign: GraphTrafficSign):
        if self.traffic_signs is None:
            self.traffic_signs = []
        self.traffic_signs.append(sign)

    def add_traffic_light(self, light: GraphTrafficLight):
        if self.traffic_lights is None:
            self.traffic_lights = []
        self.traffic_lights.append(light)
