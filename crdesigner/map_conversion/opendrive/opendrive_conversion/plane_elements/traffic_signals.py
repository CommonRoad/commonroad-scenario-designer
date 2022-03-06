"""module to capture traffic signal information from parsed opendrive file"""
import iso3166
import numpy as np
import warnings
import enum
from typing import Union

from crdesigner.map_conversion.opendrive.opendrive_parser.elements.road import Road
from crdesigner.map_conversion.common.utils import generate_unique_id

from commonroad.scenario.traffic_sign import TrafficSign, TrafficLight, TrafficSignElement, TrafficSignIDZamunda, \
    TrafficSignIDGermany, TrafficSignIDUsa, TrafficSignIDChina, TrafficSignIDSpain, TrafficSignIDRussia
from commonroad.scenario.lanelet import StopLine, LineMarking

__author__ = "Benjamin Orthen, Stefan Urban"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "0.5"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad@lists.lrz.de"
__status__ = "Released"


def extract_traffic_element_id(signal_type: str, signal_subtype: str, traffic_sign_enum: enum) \
        -> Union[TrafficSignIDZamunda, TrafficSignIDGermany, TrafficSignIDUsa, TrafficSignIDChina,
                 TrafficSignIDSpain, TrafficSignIDRussia]:
    if signal_type in set(item.value for item in traffic_sign_enum):
        element_id = traffic_sign_enum(signal_type)
    elif signal_type + "-" + signal_subtype in set(item.value for item in traffic_sign_enum):
        element_id = traffic_sign_enum(signal_type + "-" + str(signal_subtype))
    else:
        warnings.warn("OpenDRIVE/traffic_signals.py: Unknown {}"
                      " of ID {} of subtype {}!".format(traffic_sign_enum.__name__, signal_type, signal_subtype))
        element_id = traffic_sign_enum.UNKNOWN

    return element_id


def get_traffic_signals(road: Road):
    traffic_signs = []
    traffic_lights = []
    stop_lines = []

    # TODO: Stop lines are created and appended to the list for DEU and OpenDrive format.
    # This has been replicated for other countries but has not been tested with a test case
    # Stop lines have a signal type of 294 and are handled differently in the commonroad format

    for signal in road.signals:

        position, tangent, _, _ = road.planView.calc(signal.s, compute_curvature=False)
        position = np.array([position[0] + signal.t * np.cos(tangent + np.pi / 2),
                             position[1] + signal.t * np.sin(tangent + np.pi / 2)])
        if signal.dynamic == 'no':

            if signal.value == '-1' or signal.value == '-1.0000000000000000e+00' \
                    or signal.value == 'none' or signal.value is None:
                additional_values = []
            else:
                if signal.unit == 'km/h':
                    additional_values = [str(float(signal.value)/3.6)]
                else:
                    additional_values = [str(signal.value)]

            signal_country = get_signal_country(signal.country)

            if signal_country == 'DEU':
                if signal.type == "1000003" or signal.type == "1000004":
                    continue  # stop line
                    # Stop lines have a signal type of 294 and are handled differently in the commonroad format
                if signal.type == '294':
                    # Creating stop line object by first calculating the position of the two end points that define the
                    # straight stop line
                    position_1, position_2 = calculate_stop_line_position(road.lanes.lane_sections, signal,
                                                                          position, tangent)
                    stop_line = StopLine(position_1, position_2, LineMarking.SOLID)
                    stop_lines.append(stop_line)
                    continue

                element_id = extract_traffic_element_id(signal.type, str(signal.subtype), TrafficSignIDGermany)
            elif signal_country == 'USA':
                element_id = extract_traffic_element_id(signal.type, str(signal.subtype), TrafficSignIDUsa)
                if signal.type == '294':  # TODO has another ID
                    # Creating stop line object by first calculating the position of the two end points that define the
                    # straight stop line
                    position_1, position_2 = calculate_stop_line_position(road.lanes.lane_sections, signal,
                                                                          position, tangent)
                    stop_line = StopLine(position_1, position_2, LineMarking.SOLID)
                    stop_lines.append(stop_line)
                    continue

            elif signal_country == 'CHN':
                element_id = extract_traffic_element_id(signal.type, str(signal.subtype), TrafficSignIDChina)
                if signal.type == '294':  # TODO has another ID
                    # Creating stop line object by first calculating the position of the two end points that define the
                    # straight stop line
                    position_1, position_2 = calculate_stop_line_position(road.lanes.lane_sections, signal,
                                                                          position, tangent)
                    stop_line = StopLine(position_1, position_2, LineMarking.SOLID)
                    stop_lines.append(stop_line)
                    continue

            elif signal_country == 'ESP':
                element_id = extract_traffic_element_id(signal.type, str(signal.subtype), TrafficSignIDSpain)
                if signal.type == '294':  # TODO has another ID
                    # Creating stop line object by first calculating the position of the two end points that define the
                    # straight stop line
                    position_1, position_2 = calculate_stop_line_position(road.lanes.lane_sections, signal,
                                                                          position, tangent)
                    stop_line = StopLine(position_1, position_2, LineMarking.SOLID)
                    stop_lines.append(stop_line)
                    continue

            elif signal_country == 'RUS':
                element_id = extract_traffic_element_id(signal.type, str(signal.subtype), TrafficSignIDRussia)
                if signal.type == '294':  # TODO has another ID
                    # Creating stop line object by first calculating the position of the two end points that define the
                    # straight stop line
                    position_1, position_2 = calculate_stop_line_position(road.lanes.lane_sections, signal,
                                                                          position, tangent)
                    stop_line = StopLine(position_1, position_2, LineMarking.SOLID)
                    stop_lines.append(stop_line)
                    continue
            else:
                if signal.type == "1000003" or signal.type == "1000004":
                    continue
                if signal.type == '294':
                    # Creating stop line object
                    position_1, position_2 = calculate_stop_line_position(road.lanes.lane_sections, signal,
                                                                          position, tangent)
                    stop_line = StopLine(position_1, position_2, LineMarking.SOLID)
                    stop_lines.append(stop_line)
                    continue

                element_id = extract_traffic_element_id(signal.type, str(signal.subtype), TrafficSignIDZamunda)

            if element_id.value == "":
                continue
            traffic_sign_element = TrafficSignElement(
                traffic_sign_element_id=element_id,
                additional_values=additional_values
            )
            traffic_sign = TrafficSign(
                traffic_sign_id=generate_unique_id(),
                traffic_sign_elements=list([traffic_sign_element]),
                first_occurrence=None,
                position=position,
                virtual=False
            )

            traffic_signs.append(traffic_sign)

        elif signal.dynamic == 'yes':
            # the three listed here are hard to interpret in commonroad.
            # we ignore such signals in order not cause trouble in traffic simulation
            if signal.type != ("1000002" or "1000007" or "1000013"):

                traffic_light = TrafficLight(traffic_light_id=signal.id + 2000, cycle=[], position=position)

                traffic_lights.append(traffic_light)
            else:
                continue

    return traffic_lights, traffic_signs, stop_lines


def get_signal_country(signal_country: str):
    """
    ISO iso3166 standard to find 3 letter country id
    Args:
        signal_country: string value of the country
    """
    signal_country = signal_country.upper()
    if signal_country in iso3166.countries_by_name:
        return iso3166.countries_by_name[signal_country].alpha3
    elif signal_country in iso3166.countries_by_alpha2:
        return iso3166.countries_by_alpha2[signal_country].alpha3
    elif signal_country in iso3166.countries_by_alpha3:
        return signal_country
    else:
        return "ZAM"


def calculate_stop_line_position(lane_sections, signal, position, tangent):
    """
    Function to calculate the 2 points that define the stop line which
    is a straight line from one edge of the road to the other.
    Args:
        lane_sections: opendrive lane_sections list containing the lane_section parsed lane_section class
        signal: signal object in this case the stop line
        position: initial position as calculated in the get_traffic_signals function
        tangent: tangent value as calculated in the get_traffic_signals function
    """
    total_width = 0
    for lane_section in lane_sections:
        for lane in lane_section.allLanes:
            # Stop line width only depends on drivable lanes
            if lane.id != 0 and lane.type in ["driving", "onRamp", "offRamp", "exit", "entry"]:
                for width in lane.widths:
                    # Calculating total width of stop line
                    coefficients = width.polynomial_coefficients
                    lane_width = \
                        coefficients[0] + coefficients[1] * signal.s + coefficients[2] * signal.s ** 2 \
                        + coefficients[3] * signal.s ** 2

                    total_width += lane_width
    position_1 = position
    # Calculating second point of stop line using trigonometry
    position_2 = np.array([position[0] - total_width * np.cos(tangent + np.pi / 2),
                           position[1] - total_width * np.sin(tangent + np.pi / 2)])
    return position_1, position_2


def get_traffic_signal_references(road: Road):
    """
    Function to extract all the traffic sign references that are stored in the road object
    in order to avoid duplication by redefiniing predefined signals/lights and stoplines.
    """
    # TODO: This function was ultimately not used as signal references were not required to define all traffic
    #  lights signals and stoplines. However, it needs to be verified if signal references are required elsewhere.
    #  If not this function can safely be deleted.
    signal_references = []
    for signal_reference in road.signalReference:
        signal_references.append(signal_reference)
    return signal_references
