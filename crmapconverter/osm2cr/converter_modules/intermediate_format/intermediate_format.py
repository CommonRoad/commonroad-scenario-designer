"""
This module holds the classes required for the intermediate format
"""

from commonroad.scenario.obstacle import Obstacle
from typing import List, Set
from pyparsing import Dict

from crmapconverter.osm2cr.converter_modules.utility import geometry
from crmapconverter.osm2cr.converter_modules.utility.traffic_rules import TrafficSign


class Edge:
    """
    Class to represent the edges in the intermediate format
    """

    def __init__(self,
                 id: int,
                 node1: geometry.Point,
                 node2: geometry.Point,
                 left_bound: Set[geometry.Point],
                 right_bound: Set[geometry.Point],
                 additional_values: Dict):
        self.id = id
        self.node1 = node1
        self.node2 = node2
        self.leftBound = left_bound
        self.rightBound = right_bound
        self.maxspeed = additional_values['maxspeed']
        self.width = additional_values['width']


class IntermediateFormat:
    """
    Class that represents the intermediate format

    """

    def __init__(self,
                 nodes: List[geometry.Point],
                 edges: List[Edge],
                 traffic_signs: List[TrafficSign],
                 obstacles: List[Obstacle]):
        """

        :param nodes: List of nodes in the format
        :param edges: List of edges representing the roads
        :param traffic_signs: List of traffic signs on the map
        :param obstacles: List of obstacles
        """
        self.nodes = nodes
        self.edges = edges
        self.traffic_signs = traffic_signs
        self.obstacles = obstacles
