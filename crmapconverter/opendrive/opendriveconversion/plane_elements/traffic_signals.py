# -*- coding: utf-8 -*-

"""module to capture traffic signal information from parsed opendrive file"""

import numpy as np
import warnings
import enum
from typing import Union

from crmapconverter.opendrive.opendriveparser.elements.road import Road

from commonroad.scenario.traffic_sign import TrafficSign, TrafficLight, TrafficSignElement, TrafficSignIDZamunda, \
    TrafficSignIDGermany, TrafficSignIDUsa, TrafficSignIDChina, TrafficSignIDSpain, TrafficSignIDRussia


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

    for signal in road.signals:

        position, tangent = road.planView.calc(signal.s)
        position = np.array([position[0] + signal.t * np.cos(tangent + np.pi/2),
                             position[1] + signal.t * np.sin(tangent + np.pi/2)])

        if signal.dynamic == 'no':
            if signal.value == '-1' or 'none':
                additional_values = []
            else:
                additional_values = [signal.value]
            if signal.country == 'DEU':
                if signal.type == '294' or signal.type == "1000003" or signal.type == "1000004":
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
                if signal.type == '294' or signal.type == "1000003" or signal.type == "1000004":
                    continue  # stop line
                element_id = extract_traffic_element_id(signal.type, str(signal.subtype), TrafficSignIDZamunda)
            traffic_sign_element = TrafficSignElement(
                traffic_sign_element_id=element_id,
                additional_values=additional_values
            )

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

                traffic_light = TrafficLight(traffic_light_id=signal.id + 2000, cycle=[], position=position)
                traffic_lights.append(traffic_light)
            else:
                continue

    return traffic_lights, traffic_signs
