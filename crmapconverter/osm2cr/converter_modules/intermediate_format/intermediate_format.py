"""
This module holds the classes required for the intermediate format
"""
from commonroad.scenario.intersection import Intersection
from commonroad.scenario.lanelet import LaneletType, Lanelet, LaneletNetwork
from commonroad.scenario.obstacle import Obstacle
from typing import List, Set

import numpy as np
from crmapconverter.osm2cr import config
from commonroad.scenario.scenario import Scenario

from commonroad.scenario.traffic_sign import TrafficSign
from commonroad.scenario.traffic_sign import TrafficLight

from pyparsing import Dict

from build.lib.crmapconverter.osm2cr.converter_modules.graph_operations.road_graph import Graph
from crmapconverter.osm2cr.converter_modules.utility import geometry, idgenerator


class Edge:
    """
    Class to represent the edges in the intermediate format
    """

    def __init__(self,
                 id: int,
                 node1: geometry.Point,
                 node2: geometry.Point,
                 left_bound: List[np.ndarray],
                 right_bound: List[np.ndarray],
                 center_points: List[np.ndarray],
                 adjacent_right: int,
                 adjacent_right_direction_equal: bool,
                 adjacent_left: int,
                 adjacent_left_direction_equal: bool,
                 successors: List[int],
                 predecessors: List[int]):
        self.id = id
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

    def to_lanelet(self) -> Lanelet:
        return Lanelet(
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
        )

    @staticmethod
    def extract_from_lane(lane):
        current_id = lane.id
        left_bound = lane.left_bound
        right_bound = lane.right_bound
        center_points = lane.waypoints
        successors = []
        for successor in lane.successors:
            successors.append(successor.id)
        predecessors = []
        for predecessor in lane.predecessors:
            predecessors.append(predecessor.id)
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

        successors = [successor.id for successor in lane.successors]
        predecessors = [predecessor.id for predecessor in lane.predecessors]
        return Edge(current_id,
                    lane.from_node.get_point(),
                    lane.to_node.get_point(),
                    lane.left_bound,
                    lane.right_bound,
                    lane.waypoints,
                    adjacent_right,
                    adjacent_right_direction_equal,
                    adjacent_left,
                    adjacent_left_direction_equal,
                    successors,
                    predecessors,
                    )


class IntermediateFormat:
    """
    Class that represents the intermediate format

    """

    def __init__(self,
                 nodes: List[geometry.Point],
                 edges: List[Edge],
                 traffic_signs: List[TrafficSign] = None,
                 traffic_lights: List[TrafficLight] = None,
                 obstacles: List[Obstacle] = None):
        """

        :param nodes: List of nodes in the format
        :param edges: List of edges representing the roads
        :param traffic_signs: List of traffic signs on the map
        :param obstacles: List of obstacles
        """

        self.nodes = nodes
        self.edges = edges
        self.traffic_signs = traffic_signs
        self.traffic_lights = traffic_lights
        self.obstacles = obstacles

    def to_commonroad_scenario(self):
        scenario = Scenario(config.TIMESTEPSIZE, config.BENCHMARK_ID)
        net = LaneletNetwork()
        for edge in self.edges:
            lanelet = edge.to_lanelet()
            net.add_lanelet(lanelet)

        for sign in self.traffic_signs:
            net.add_traffic_sign(sign, set())
        scenario.lanelet_network = net
        return scenario

    @staticmethod
    def extract_road_graph(graph):
        road_graph = graph
        nodes = [node.get_point() for node in road_graph.nodes]
        edges = []
        lanes = graph.get_all_lanes()
        for lane in lanes:
            edge = Edge.extract_from_lane(lane)
            edges.append(edge)

        traffic_signs = [sign.to_traffic_sign_cr() for sign in graph.traffic_signs]
        #traffic_lights = [light.to_traffic_light_cr() for light in graph.traffic_lights]
        return IntermediateFormat(nodes,
                                  edges,
                                  traffic_signs)
