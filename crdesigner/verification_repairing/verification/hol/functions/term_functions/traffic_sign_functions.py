from typing import List

from commonroad.scenario.lanelet import Lanelet
from commonroad.scenario.traffic_sign import TrafficSign, TrafficSignElement
from shapely import Point


def traffic_sign_id(traffic_sign: TrafficSign) -> int:
    """
    Returns ID of the traffic sign.

    :param traffic_sign: Traffic sign.
    :return: ID of traffic sign.
    """
    return traffic_sign.traffic_sign_id


def traffic_sign_elements(traffic_sign: TrafficSign) -> List[TrafficSignElement]:
    """
    Returns the traffic sign elements of the traffic sign.

    :param traffic_sign: Traffic sign.
    :return: Traffic sign elements.
    """
    return traffic_sign.traffic_sign_elements


def distance_to_lanelet(traffic_sign: TrafficSign, lanelet: Lanelet) -> int:
    """
    Returns the distance between the traffic sign and the lanelet.

    :param traffic_sign: Traffic sign.
    :param lanelet: Lanelet.
    :return: Distance.
    """
    if traffic_sign.position is None:
        distance = 0.0
    else:
        distance = lanelet.polygon.shapely_object.distance(Point(traffic_sign.position))

    return distance
