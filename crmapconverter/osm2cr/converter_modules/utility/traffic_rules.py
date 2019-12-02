"""
This module provides various classes to handle traffic rules.
"""
from enum import Enum

from typing import List
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

