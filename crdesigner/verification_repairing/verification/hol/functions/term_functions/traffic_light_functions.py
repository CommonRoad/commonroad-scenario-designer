from typing import List

from commonroad.scenario.traffic_light import TrafficLight, TrafficLightCycleElement


def traffic_light_id(traffic_light: TrafficLight) -> int:
    """
    Returns ID of the traffic light.

    :param traffic_light: Traffic light.
    :return: ID of traffic light.
    """
    return traffic_light.traffic_light_id


def cycle_elements(traffic_light: TrafficLight) -> List[TrafficLightCycleElement]:
    """
    Returns the cycle elements of the traffic light.

    :param traffic_light: Traffic light.
    :return: Cycle elements.
    """
    return traffic_light.traffic_light_cycle.cycle_elements


def duration(cycle_element: TrafficLightCycleElement) -> int:
    """
    Returns the duration of the cycle element.

    :param cycle_element: Cycle element.
    :return: Duration.
    """
    return cycle_element.duration
