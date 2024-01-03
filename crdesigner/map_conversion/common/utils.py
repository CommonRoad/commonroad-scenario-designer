import warnings

import mgrs
from commonroad.scenario.traffic_light import (
    TrafficLightCycle,
    TrafficLightCycleElement,
    TrafficLightState,
)


def generate_unique_id(set_id: int = None) -> int:
    """
    Generates unique ID using a function counter.

    :param set_id ID which should be set.
    :return: new unique ID

    """
    if not hasattr(generate_unique_id, "counter"):
        generate_unique_id.counter = 0  # it doesn't exist yet, so initialize it
    if set_id is not None:
        generate_unique_id.counter = set_id
        return generate_unique_id.counter
    generate_unique_id.counter += 1
    return generate_unique_id.counter


def convert_to_new_lanelet_id(old_lanelet_id: str, ids_assigned: dict) -> int:
    """
    Convert the old lanelet ids (format 501.1.-1.-1) to newer, simpler ones (100, 101 etc.).
    Save the assignments in the dict which is passed to the function as ids_assigned.

    :param old_lanelet_id: Old id with format '501.1.-1.-1'
    :param ids_assigned: Dict with all previous assignments
    :return: The new lanelet id
    """

    if old_lanelet_id in ids_assigned.keys():
        new_lanelet_id = ids_assigned[old_lanelet_id]
    else:
        new_lanelet_id = generate_unique_id()
        ids_assigned[old_lanelet_id] = new_lanelet_id

    return new_lanelet_id


def get_default_cycle() -> TrafficLightCycle:
    """
    Defines default traffic light cycle in case no cycle is provided

    _:returns traffic light cycle element
    """
    cycle = [
        (TrafficLightState.RED, 60),
        (TrafficLightState.RED_YELLOW, 10),
        (TrafficLightState.GREEN, 60),
        (TrafficLightState.YELLOW, 10),
    ]
    cycle_element_list = [TrafficLightCycleElement(state[0], state[1]) for state in cycle]
    return TrafficLightCycle(cycle_element_list)


def clean_projection_string(proj_str: str) -> str:
    """
    Removes parts from projection string which are not supported by our used projection package.

    :param proj_str: Original projection string.
    :returns: Updated projection string.
    """
    final_str = ""
    if "geoidgrids" in proj_str:
        for tmp_str in proj_str.split("+"):
            if "geoidgrids" in tmp_str:
                warnings.warn("geoidgrids removed from projection string")
                continue
            final_str += f"+{tmp_str}" if tmp_str != "" else ""
    else:
        final_str = proj_str
    final_str = final_str.replace("\n", "").lstrip().rstrip()
    return final_str


def create_mgrs_code(lat: float, lon: float) -> str:
    """
    Creates the MGRS code of the provided lat/lon position

    :param lat: lateral WGS84 position
    :param lon: longitudinal WGS84 position
    :return: mgrs code of position as string
    """
    mgrs_converter = mgrs.MGRS()
    mgrs_code = mgrs_converter.toMGRS(latitude=lat, longitude=lon)

    return mgrs_code
