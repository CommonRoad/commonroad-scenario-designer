# -*- coding: utf-8 -*-

"""module to capture traffic signal information from parsed opendrive file"""

import numpy as np
import warnings
import enum
from typing import Union

from crmapconverter.opendrive.opendriveparser.elements.road import Road

from commonroad.scenario.traffic_sign import TrafficSign, TrafficLight, TrafficSignElement, TrafficSignIDZamunda, \
    TrafficSignIDGermany, TrafficSignIDUsa, TrafficSignIDChina, TrafficSignIDSpain, TrafficSignIDRussia
from commonroad.scenario.lanelet import StopLine, LineMarking


def extract_traffic_element_id(signal_type: str, singal_subtype: str, traffic_sign_enum: enum) \
        -> Union[TrafficSignIDZamunda, TrafficSignIDGermany, TrafficSignIDUsa, TrafficSignIDChina,
                 TrafficSignIDSpain, TrafficSignIDRussia]:
    if signal_type in set(item.value for item in traffic_sign_enum):
        element_id = traffic_sign_enum(signal_type)
    elif signal_type + "-" + singal_subtype in set(item.value for item in traffic_sign_enum):
        element_id = traffic_sign_enum(signal_type + "-" + str(singal_subtype))
    else:
        warnings.warn("OpenDRIVE/traffic_signals.py: Unknown {}"
                      " of ID {} of subtype {}!".format(traffic_sign_enum.__name__, signal_type, singal_subtype))
        element_id = traffic_sign_enum.UNKNOWN

    return element_id


def get_traffic_signals(road: Road):
    traffic_signs = []
    traffic_lights = []
    stop_lines = []

    # This map will help us convert the id's in the signal_reference list
    # to the new id that are assigned in this function

    old_signal_id_to_new_id_mapper = dict()

    for signal in road.signals:


        position, tangent = road.planView.calc(signal.s)
        position = np.array([position[0] + signal.t * np.cos(tangent + np.pi / 2),
                             position[1] + signal.t * np.sin(tangent + np.pi / 2)])
        if signal.dynamic == 'no':

            if signal.value == '-1' or 'none':
                additional_values = []
            else:
                additional_values = [signal.value]
            if signal.country == 'DEU':
                if signal.type == "1000003" or signal.type == "1000004":
                    continue  # stop line
                    # Stop lines have a signal type of 294 and are handled differently in the commonroad format

                if signal.type == '294':
                    # Creating stop line object
                    position_1, position_2 = calculate_stop_line_position(road.lanes.lane_sections, signal,
                                                                          position, tangent)
                    stop_line = StopLine(position_1, position_2, LineMarking.SOLID)
                    stop_lines.append(stop_line)
                    continue  # stop line

                element_id = extract_traffic_element_id(signal.type, str(signal.subtype), TrafficSignIDGermany)
            elif signal.country == 'USA':
                element_id = extract_traffic_element_id(signal.type, str(signal.subtype), TrafficSignIDUsa)
            elif signal.country == 'CHN':
                element_id = extract_traffic_element_id(signal.type, str(signal.subtype), TrafficSignIDChina)
            elif signal.country == 'ESP':
                element_id = extract_traffic_element_id(signal.type, str(signal.subtype), TrafficSignIDSpain)
            elif signal.country == 'RUS':
                element_id = extract_traffic_element_id(signal.type, str(signal.subtype), TrafficSignIDRussia)
            else:
                if signal.type == "1000003" or signal.type == "1000004":
                    continue

                # Stop lines have a signal type of 294 and are handled differently in the commonroad format
                if signal.type == '294':
                    # Creating stop line object
                    position_1, position_2 = calculate_stop_line_position(road.lanes.lane_sections, signal,
                                                                          position, tangent)
                    stop_line = StopLine(position_1, position_2, LineMarking.SOLID)
                    stop_lines.append(stop_line)
                    old_signal_id_to_new_id_mapper[signal.id] = [stop_line, "stop line"]

                    continue  # stop line
                element_id = extract_traffic_element_id(signal.type, str(signal.subtype), TrafficSignIDZamunda)
            traffic_sign_element = TrafficSignElement(
                traffic_sign_element_id=element_id,
                additional_values=additional_values
            )
            old_signal_id_to_new_id_mapper[signal.id] = [int(
                "".join([str(road.id), str(signal.id), str(abs(int(position[0]))),
                         str(abs(int(position[1]))), str(abs(int(signal.s)))])), "traffic sign"]

            traffic_sign = TrafficSign(
                traffic_sign_id=int("".join([str(road.id), str(signal.id), str(abs(int(position[0]))),
                                             str(abs(int(position[1]))), str(abs(int(signal.s)))])),
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
                old_signal_id_to_new_id_mapper[signal.id] = [signal.id + 2000, "traffic light"]

                traffic_light = TrafficLight(traffic_light_id=signal.id + 2000, cycle=[], position=position)

                traffic_lights.append(traffic_light)
            else:
                continue

    return traffic_lights, traffic_signs, stop_lines, old_signal_id_to_new_id_mapper


def calculate_stop_line_position(lane_sections, signal, position, tangent):
    """
    Function to calculate the 2 points that define the stop line which
    is a straight line from one edge of the road to the other.
    """
    total_width = 0
    for lane_section in lane_sections:
        for lane in lane_section.allLanes:
            # Stop line width only depends on drivable lanes
            if lane.id != 0 and lane.type in ["driving", "onRamp", "offRamp", "exit", "entry"]:
                for width in lane.widths:
                    # Calculating total width of stop line
                    coefficients = width.polynomial_coefficients
                    lane_width = coefficients[0] + coefficients[1] * signal.s + coefficients[2] * signal.s ** 2 + \
                                 coefficients[3] * signal.s ** 2

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
    signal_references = []
    for signal_reference in road.signalReference:
        signal_references.append(signal_reference)

    return signal_references
