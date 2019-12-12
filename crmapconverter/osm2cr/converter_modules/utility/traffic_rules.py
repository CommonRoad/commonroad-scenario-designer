"""
This module provides various classes to handle traffic rules.
"""
import enum
from abc import ABC
from typing import List

from crmapconverter.osm2cr.config import TrafficSignID
from crmapconverter.osm2cr.converter_modules.utility.geometry import Point
from pyparsing import Dict

from crmapconverter.osm2cr.converter_modules.utility import geometry


@enum.unique
class Direction(enum.Enum):
    """
    Enum for all the possible directions for a traffic signal
    """
    LEFT = "left"
    RIGHT = "right"
    FORWARD = "forward"
    BACKWARD = "backward"


@enum.unique
class Signal(enum.Enum):
    """
    Enum for the possible types of traffic light in signals
    """
    RED = "red"
    YELLOW = "yellow"
    REDYELLOW = "redYellow"
    GREEN = "green"


class TrafficLight:
    """
    Class for the traffic lights in a traffic signal
    """
    def __init__(self, signal, time):
        """

        :param signal: signal light color
        :param time: time segment for the traffic light
        """
        self.signal = signal
        self.time = time


class TrafficSignElement:
    """Class to represent one unit of traffic sign"""
    def __init__(self, trafficSignID: str,
                 additionalValue: List[int]):
        self.trafficSignID = trafficSignID
        self.additionalValue = additionalValue

    def __str__(self):
        return f"Sign Element with id {self.trafficSignID} and values {self.additionalValue} "

    def __repr__(self):
        return f"Sign Element with id {self.trafficSignID} and values {self.additionalValue} "


class TrafficSign:
    """
    Class to represent Traffic Signs
    """

    def __init__(self,
                 id: int,
                 position: geometry.Point,
                 traffic_sign_elements: List[TrafficSignElement],
                 virtual = False):
        """

        :param id: int for the id of the sign
        :param position: location of the signal
        :param traffic_sign_elements: list of traffic sign elements
        :param virtual: boolean value
        """
        self.id = id
        self.position = position
        self.traffic_sign_elements = traffic_sign_elements
        self.virtual = virtual

    def update(self, data):
        key = data['k']
        value = data['v']
        has_value = True
        sign_id = TrafficSign.map_sign_id(key)
        if sign_id == TrafficSignID.UNKNOWN.value:
            sign_id = TrafficSign.map_sign_id(value)
            has_value = False

        # add new element
        added = False
        for element in self.traffic_sign_elements:
            if element.trafficSignID == sign_id and has_value:
                element.additionalValue.append(value)
                added = True
                break
        if not added:
            # new element
            values = []
            if has_value:
                values.append(value)
            element = TrafficSignElement(sign_id, values)
            self.traffic_sign_elements.append(element)

    @classmethod
    def map_sign_id(cls, value):
        if value == 'stop':
            return TrafficSignID.STOP.value
        elif value == 'give_way':
            return TrafficSignID.GIVEWAY.value
        elif value == 'city_limit':
            return TrafficSignID.CITYLIMIT.value
        else:
            return TrafficSignID.UNKNOWN.value

    def __str__(self):
        return f"Sign At {self.position} with {self.traffic_sign_elements} "




class TrafficLight:
    """
    Class to represent the traffic lights
    """

    def __init__(self, id: int, position: geometry.Point):
        """

        :param id: id of the signal
        :param position: point coordinates of the signal
        """
        self.id = id
        self.position = position
        self.cycle = []
        self.offset = 0
        self.direction = Direction.FORWARD
        self.active = True

    def update(self, data):
        key = data['k']
        value = data['v']
        if key == 'traffic_signals:direction':
            self.direction = Direction.FORWARD if value == "forward" else Direction.BACKWARD

    def __str__(self):
        return f"Traffic Light At {self.position}"


def get_traffic_sign_from_osm_data(data, position, id):
    """
    Returns new Traffic Sign object from the data, position and id
    :param data: key-value pair extracted from the tag in osm
    :param position: point of the traffic sign
    :param id: id of the traffic sign
    :return: TrafficSign object
    """
    key = data['k']
    value = data['v']
    if value == "traffic_signals":
        # the data is pointing to a traffic signal
        return TrafficLight(id, position)
    if key == "maxspeed":
        # the data consists of maxspeed limit
        element = TrafficSignElement(TrafficSignID.MAXSPEED.value, [value])
        return TrafficSign(id, position,  [element])
    if key == "traffic_sign":
        # the data is a sign
        sign_id = TrafficSign.map_sign_id(value)
        element = TrafficSignElement(sign_id, [])
        return TrafficSign(id, position, [element])


def create_sign_from_osm(extracted_rules, points):
    """
    :param extracted_rules: Extracted rules in the osm in the form of Dict {point_id : {key-value pairs}}
    :param points: List of points in the osm
    :return: Dict of traffic sign objects
    """
    traffic_rules = {}
    for rule in extracted_rules:
        for point_id in rule:
            if point_id in traffic_rules:
                # rule will give additional information on an already added point
                traffic_rules[point_id].update(rule[point_id])
            else:
                # create a traffic sign to add on this point
                traffic_sign = get_traffic_sign_from_osm_data(rule[point_id], points[point_id], point_id)
                traffic_rules.update({point_id: traffic_sign})
    return traffic_rules


