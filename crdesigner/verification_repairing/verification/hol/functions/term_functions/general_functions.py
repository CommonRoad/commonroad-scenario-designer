from typing import Union

from commonroad.scenario.intersection import Intersection
from commonroad.scenario.lanelet import Lanelet
from commonroad.scenario.traffic_light import TrafficLight
from commonroad.scenario.traffic_sign import TrafficSign


def el_id(element: Union[Lanelet, TrafficSign, TrafficLight, Intersection]) -> int:
    """
    Returns the ID of the given element.

    :param element: One of Lanelet, TrafficSign, TrafficLight, Intersection.
    :return: Element ID.
    """
    if type(element) is Lanelet:
        return element.lanelet_id
    if type(element) is TrafficSign:
        return element.traffic_sign_id
    if type(element) is TrafficLight:
        return element.traffic_light_id
    if type(element) is Intersection:
        return element.intersection_id
    # if type(element) is IncomingGroup:
    # return element.incoming_id
    # if type(element) is OutgoingGroup:
    # return element.outgoing_id
    # if type(element) is StopLine:
    # return element.stop_line_id
