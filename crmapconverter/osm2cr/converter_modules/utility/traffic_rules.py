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
    FORWARD = "forward"
    BACKWARD = "backward"


class Signal(Enum):
    """
    Enum for the possible types of traffic light in signals
    """
    RED: "red"
    YELLOW: "yellow"
    REDYELLOW: "redYellow"
    GREEN: "green"

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

    def update(self, data):
        key = data['k']
        value = data['v']
        if key == 'traffic_sign' and value != "maxspeed":
            self.additional_values.update({value: True})
        else:
            self.additional_values.update({key: value})

    def __str__(self):
        return f"Sign At {self.position} with {self.additional_values} "


class TrafficSignal(TrafficSign):
    """
    Class to represent the traffic signals
    """

    def __init__(self, id: str, position: geometry.Point):
        """

        :param id: id of the signal
        :param position: point coordinates of the signal
        """
        super().__init__(id, position, {})
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
        return f"Signal At {self.position}"

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
        return TrafficSignal(id, position)
    if key == "maxspeed":
        # the data consists of maxspeed limit
        return TrafficSign(id, position, {key: value})
    if key == "traffic_sign":
        # the data is a sign
        return TrafficSign(id, position, {value: True})


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


