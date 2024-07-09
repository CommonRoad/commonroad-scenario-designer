import enum
import logging
from typing import Dict, List, Tuple, Union

import numpy as np
from commonroad.scenario.lanelet import LineMarking, StopLine
from commonroad.scenario.traffic_light import TrafficLight, TrafficLightDirection
from commonroad.scenario.traffic_sign import (
    TrafficSign,
    TrafficSignElement,
    TrafficSignIDChina,
    TrafficSignIDGermany,
    TrafficSignIDRussia,
    TrafficSignIDSpain,
    TrafficSignIDUsa,
    TrafficSignIDZamunda,
)

from crdesigner.map_conversion.common.utils import generate_unique_id, get_default_cycle
from crdesigner.map_conversion.opendrive.opendrive_conversion import utils
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.road import Road
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadLanes import (
    LaneSection,
)
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadSignal import (
    Signal,
)


def extract_traffic_element_id(signal_type: str, signal_subtype: str, traffic_sign_enum: enum) -> Union[
    TrafficSignIDZamunda,
    TrafficSignIDGermany,
    TrafficSignIDUsa,
    TrafficSignIDChina,
    TrafficSignIDSpain,
    TrafficSignIDRussia,
]:
    """Extract the traffic element id from the signal type and subtype string.

    :param signal_type: Signal type of the traffic element
    :param signal_subtype: Subtype of the traffic element
    :param traffic_sign_enum: Enumeration of country-specific traffic signs
    :return: The extracted traffic element id.
    """
    if signal_type in set(item.value for item in traffic_sign_enum):
        element_id = traffic_sign_enum(signal_type)
    elif signal_type + "-" + signal_subtype in set(item.value for item in traffic_sign_enum):
        element_id = traffic_sign_enum(signal_type + "-" + str(signal_subtype))
    elif (
        traffic_sign_enum is TrafficSignIDGermany or traffic_sign_enum is TrafficSignIDZamunda
    ) and signal_type == "252":  # traffic sign ID 252 is replaced by 260
        element_id = traffic_sign_enum("260")
    else:
        logging.warning(
            "OpenDRIVE/traffic_signals.py: Unknown {} of ID {} of subtype {}!".format(
                traffic_sign_enum.__name__, signal_type, signal_subtype
            )
        )
        element_id = traffic_sign_enum.UNKNOWN

    return element_id


def assign_traffic_signals_to_road(road: Road, traffic_light_dirs: Dict[str, List[str]],
                                   traffic_light_lanes: Dict[str, List[Tuple[int, int]]]):
    """Extracts traffic_lights, traffic_signs, stop_lines from a road.

    :param road: The road object from which to extract signals.
    """
    # TODO: Stop lines are created and appended to the list for DEU and OpenDrive format.
    # This has been replicated for other countries but has not been tested with a test case
    # Stop lines have a signal type of 294 and are handled differently in the commonroad format
    for signal in road.signals:
        lanes = (0, 0) if signal.validity_from is None else (signal.validity_from, signal.validity_to)
        position, tangent, _, _ = road.plan_view.calc(signal.s, compute_curvature=False)
        position = np.array(
            [position[0] + signal.t * np.cos(tangent + np.pi / 2), position[1] + signal.t * np.sin(tangent + np.pi / 2)]
        )
        if signal.dynamic == "no":
            if (
                signal.signal_value == "-1"
                or signal.signal_value == "-1.0000000000000000e+00"
                or signal.signal_value == "none"
                or signal.signal_value is None
            ):
                additional_values = []
            else:
                if signal.unit == "km/h":
                    additional_values = [str(float(signal.signal_value) / 3.6)]
                else:
                    additional_values = [str(signal.signal_value)]

            signal_country = utils.get_signal_country(signal.country)

            if signal_country == "DEU":
                if signal.type == "1000003" or signal.type == "1000004":
                    continue
                element_id = extract_traffic_element_id(signal.type, str(signal.subtype), TrafficSignIDGermany)
                extract_stop_line("294", signal, road, position, tangent, lanes)
            elif signal_country == "USA":
                element_id = extract_traffic_element_id(signal.type, str(signal.subtype), TrafficSignIDUsa)
                extract_stop_line("294", signal, road, position, tangent, lanes)  # TODO has another ID than 294
            elif signal_country == "CHN":
                element_id = extract_traffic_element_id(signal.type, str(signal.subtype), TrafficSignIDChina)
                extract_stop_line("294", signal, road, position, tangent, lanes)  # TODO has another ID than 294
            elif signal_country == "ESP":
                element_id = extract_traffic_element_id(signal.type, str(signal.subtype), TrafficSignIDSpain)
                extract_stop_line("294", signal, road, position, tangent, lanes)  # TODO has another ID than 294
            elif signal_country == "RUS":
                element_id = extract_traffic_element_id(signal.type, str(signal.subtype), TrafficSignIDRussia)
                extract_stop_line("294", signal, road, position, tangent, lanes)  # TODO has another ID than 294
            else:
                if signal.type == "1000003" or signal.type == "1000004":
                    continue
                element_id = extract_traffic_element_id(signal.type, str(signal.subtype), TrafficSignIDZamunda)
                extract_stop_line("294", signal, road, position, tangent, lanes)  # TODO has another ID than 294

            if element_id.value == "":
                continue
            traffic_sign_element = TrafficSignElement(
                traffic_sign_element_id=element_id, additional_values=additional_values
            )
            traffic_sign = TrafficSign(
                traffic_sign_id=generate_unique_id(),
                traffic_sign_elements=list([traffic_sign_element]),
                first_occurrence=None,
                position=position,
                virtual=False,
            )

            road.add_traffic_sign((traffic_sign, lanes))

        elif signal.dynamic == "yes":
            # the three listed here are hard to interpret in commonroad.
            # we ignore such signals in order not cause trouble in traffic simulation
            tdir = TrafficLightDirection.ALL
            if traffic_light_dirs[signal.signal_id] is not None:
                for tid, t_light in traffic_light_dirs.items():
                    if "Right" in t_light and "Straight" in t_light and "Left" in t_light:
                        tdir = TrafficLightDirection.ALL
                    elif "Left" in t_light and "Straight" in t_light:
                        tdir = TrafficLightDirection.LEFT_STRAIGHT
                    elif "Right" in t_light and "Straight" in t_light:
                        tdir = TrafficLightDirection.STRAIGHT_RIGHT
                    elif "Left" in t_light and "Right" in t_light:
                        tdir = TrafficLightDirection.LEFT_RIGHT
                    elif "Left" in t_light:
                        tdir = TrafficLightDirection.LEFT
                    elif "Right" in t_light:
                        tdir = TrafficLightDirection.RIGHT
                    elif "Straight" in t_light:
                        tdir = TrafficLightDirection.STRAIGHT
                    else:
                        tdir = TrafficLightDirection.ALL
            lanes = lanes if traffic_light_lanes[signal.signal_id] is None else traffic_light_lanes[signal.signal_id]
            if signal.type != ("1000002" or "1000007" or "1000013"):
                traffic_light = TrafficLight(
                    traffic_light_id=generate_unique_id(), position=position, traffic_light_cycle=get_default_cycle(),
                        direction=tdir)  # TODO remove for new CR-Format
                road.add_traffic_light((traffic_light, lanes))
            else:
                continue


def extract_stop_line(signal_id: str, signal: Signal, road: Road, position: np.ndarray, tangent: float, lanes: Tuple[int, int]):
    if signal.type == signal_id:  # TODO has another ID
        # Creating stop line object by first calculating the position of the two end points that define the
        # straight stop line
        position_1, position_2 = calculate_stop_line_position(road.lanes.lane_sections, signal, position, tangent)
        stop_line = StopLine(position_1, position_2, LineMarking.SOLID)
        road.add_stop_line((stop_line, lanes))


def calculate_stop_line_position(
    lane_sections: List[LaneSection], signal: Signal, position: np.ndarray, tangent: float
) -> Tuple[np.ndarray, np.ndarray]:
    """Function to calculate the 2 points that define the stop line which
    is a straight line from one edge of the road to the other.

    :param lane_sections: Opendrive lane_sections list containing the lane_section parsed lane_section class
    :param signal: Signal object, in this case the stop line.
    :param position: initial position as calculated in the get_traffic_signals function
    :param tangent: tangent value as calculated in the get_traffic_signals function
    :return: Positions of the stop line
    """
    total_width = 0
    for lane_section in lane_sections:
        for lane in lane_section.all_lanes:
            # Stop line width only depends on drivable lanes
            if lane.id != 0 and lane.type in ["driving", "onRamp", "offRamp", "exit", "entry"]:
                for width in lane.widths:
                    # Calculating total width of stop line
                    coefficients = width.polynomial_coefficients
                    lane_width = (
                        coefficients[0]
                        + coefficients[1] * signal.s
                        + coefficients[2] * signal.s**2
                        + coefficients[3] * signal.s**3
                    )

                    total_width += lane_width
    position_1 = position
    # Calculating second point of stop line using trigonometry
    position_2 = np.array(
        [
            position[0] - total_width * np.cos(tangent + np.pi / 2),
            position[1] - total_width * np.sin(tangent + np.pi / 2),
        ]
    )
    return position_1, position_2


def  get_traffic_signal_references(
    road: Road, traffic_light_dirs: Dict[str, List[str]], traffic_light_lanes: Dict[str, List[Tuple[int, int]]]
):
    """Function to extract relevant information from sign references."""
    for signal in road.signal_reference:
        if traffic_light_dirs.get(signal.signal_id) is not None:
            traffic_light_dirs[signal.signal_id].append(signal.turn_relation)
            traffic_light_lanes[signal.signal_id].append((signal.validity_to, signal.validity_from))
