from commonroad.scenario.traffic_light import TrafficLight, TrafficLightCycleElement


def has_cycle_element(traffic_light: TrafficLight, cycle_element: TrafficLightCycleElement) -> bool:
    """
    Checks whether the traffic light has the cycle element.

    :param traffic_light: Traffic light.
    :param cycle_element: Cycle element.
    :return: Boolean indicates whether the traffic light has the cycle element.
    """
    for cycle_elm in traffic_light.traffic_light_cycle.cycle_elements:
        if cycle_elm == cycle_element:
            return True

    return False
