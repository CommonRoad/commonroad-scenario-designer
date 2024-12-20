"""
This module holds the classes required for the intermediate format
"""

__author__ = "Behtarin Ferdousi"

import warnings
from typing import List, Set

import numpy as np
from commonroad.scenario.lanelet import Lanelet, LaneletType, LineMarking

from crdesigner.common.config.osm_config import osm_config as config

from ._intermediate_node import Node


class Edge:
    """
    Class to represent the edges in the intermediate format
    """

    def __init__(
        self,
        edge_id: int,
        node1: Node,
        node2: Node,
        left_bound: List[np.ndarray],
        right_bound: List[np.ndarray],
        center_points: List[np.ndarray],
        adjacent_right: int,
        adjacent_right_direction_equal: bool,
        adjacent_left: int,
        adjacent_left_direction_equal: bool,
        successors: List[int],
        predecessors: List[int],
        traffic_signs: Set[int],
        traffic_lights: Set[int],
        edge_type: str = config.LANELETTYPE,
    ):
        """
        Initialize an edge

        :param edge_id: unique id for edge
        :param node1: node at the start of the edge
        :param node2: node at the end of the edge
        :param left_bound: list of vertices on the left bound of edge
        :param right_bound: list of vertices on the right bound of edge
        :param center_points: list of center vertices of the edge
        :param adjacent_right: id of the adjacent right edge
        :param adjacent_right_direction_equal: true if adjacent right edge has
        the same direction, false otherwise
        :param adjacent_left: id of the adjacent left edge
        :param adjacent_left_direction_equal: true if adjacent left edge has
        the same direction, false otherwise
        :param successors: List of ids of the succcessor edges
        :param predecessors: List of ids of the predecessor edges
        :param traffic_signs: Set of id of traffic signs applied on the edge
        :param traffic_lights: Set of id of traffic lights applied on the edge
        """
        self.id = edge_id
        self.node1 = node1
        self.node2 = node2
        self.left_bound = left_bound
        self.right_bound = right_bound
        self.center_points = center_points
        self.adjacent_right = adjacent_right
        self.adjacent_left_direction_equal = adjacent_left_direction_equal
        self.adjacent_left = adjacent_left
        self.adjacent_right_direction_equal = adjacent_right_direction_equal
        self.successors = successors
        self.predecessors = predecessors
        self.traffic_signs = traffic_signs
        self.traffic_lights = traffic_lights
        self.edge_type = edge_type

    def is_valid(self, lanelet) -> bool:
        """
        Checks if shape of a given lanelet is valid for CommonRoad

        :return: boolean if given lanelet is valid
        """
        polygon = lanelet.polygon.shapely_object
        if not polygon.is_valid:
            warnings.warn("Lanelet " + str(lanelet.lanelet_id) + " invalid")
            return False
        return True

    def to_lanelet(self) -> Lanelet:
        """
        Converts to CommonRoad Lanelet object

        :return: CommonRoad Lanelet
        """
        lanelet = Lanelet(
            np.array(self.left_bound),
            np.array(self.center_points),
            np.array(self.right_bound),
            self.id,
            self.predecessors,
            self.successors,
            self.adjacent_left,
            self.adjacent_left_direction_equal,
            self.adjacent_right,
            self.adjacent_right_direction_equal,
            traffic_signs=self.traffic_signs,
            traffic_lights=self.traffic_lights,
            lanelet_type={LaneletType(self.edge_type)},
            line_marking_left_vertices=LineMarking.UNKNOWN,
            line_marking_right_vertices=LineMarking.UNKNOWN,
        )
        self.is_valid(lanelet)
        return lanelet

    @staticmethod
    def extract_from_lane(lane) -> "Edge":
        """
        Initialize edge from the RoadGraph lane element
        :param lane: Roadgraph.lane
        :return: Edge element for the Intermediate Format
        """
        current_id = lane.id

        successors = [successor.id for successor in lane.successors]
        predecessors = [predecessor.id for predecessor in lane.predecessors]

        # left adjacent
        if lane.adjacent_left is not None:
            adjacent_left = lane.adjacent_left.id
            if lane.adjacent_left_direction_equal is not None:
                adjacent_left_direction_equal = lane.adjacent_left_direction_equal
            elif lane.edge is not None:
                adjacent_left_direction_equal = lane.forward == adjacent_left.forward
            else:
                raise ValueError("Lane has no direction info!")
        else:
            adjacent_left = None
            adjacent_left_direction_equal = None

        # right adjacent
        if lane.adjacent_right is not None:
            adjacent_right = lane.adjacent_right.id
            if lane.adjacent_right_direction_equal is not None:
                adjacent_right_direction_equal = lane.adjacent_right_direction_equal
            elif lane.edge is not None:
                adjacent_right_direction_equal = lane.forward == adjacent_right.forward
            else:
                raise ValueError("Lane has no direction info!")
        else:
            adjacent_right = None
            adjacent_right_direction_equal = None

        traffic_lights = set()
        if lane.traffic_lights is not None:
            traffic_lights = {light.id for light in lane.traffic_lights}

        traffic_signs = set()
        if lane.traffic_signs is not None:
            traffic_signs = {sign.id for sign in lane.traffic_signs}

        from_node = Node(lane.from_node.id, lane.from_node.get_point())
        to_node = Node(lane.to_node.id, lane.to_node.get_point())

        return Edge(
            current_id,
            from_node,
            to_node,
            lane.left_bound,
            lane.right_bound,
            lane.waypoints,
            adjacent_right,
            adjacent_right_direction_equal,
            adjacent_left,
            adjacent_left_direction_equal,
            successors,
            predecessors,
            traffic_signs,
            traffic_lights,
        )
