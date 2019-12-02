"""
This module holds the classes required for the intermediate format
"""
from enum import Enum

from commonroad.scenario.obstacle import Obstacle
from typing import List, Set
from pyparsing import Dict

from crmapconverter.osm2cr.converter_modules.utility import geometry


class Direction(Enum):
    """
    Enum for all the possible directions for a traffic signal
    """
    LEFT = "left"
    RIGHT = "right"
    STRAIGHT = "straight"


class Signal(Enum):
    """
    Enum for the possible types of traffic light in signals
    """
    RED: "red"
    YELLOW: "yellow"
    REDYELLOW: "redYellow"
    GREEN: "green"


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


class TrafficSign:
    """
    Class to represent Traffic Signs
    """

    def __init__(self,
                 id: str,
                 position: geometry.Point,
                 additional_values: Dict):
        """

        :param id: string for id of the sign: COUNTRYCODE:id
        :param position: location of the signal
        :param additional_values: key-value pair of additional values
        """
        self.id = id
        self.position = position
        self.additional_values = additional_values


class TrafficSignal(TrafficSign):
    """
    Class to represent the traffic signals
    """

    def __init__(self,
                 id: str,
                 position: geometry.Point,
                 cycle: List[(Signal, int)],
                 offset: int,
                 direction: Direction,
                 active: bool):
        """

        :param id: string for the id
        :param position: point for the location
        :param cycle: list of tuple of signal and respective time segment
        :param offset: time offset for the signal cycle
        :param direction: applicable direction
        :param active: is active or not
        """
        self.id = id
        self.position = position
        self.cycle = cycle
        self.offset = offset
        self.direction = direction
        self.active = active


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
