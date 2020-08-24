# -*- coding: utf-8 -*-

"""module to capture traffic signal information from parsed opendrive file"""

import numpy as np
import warnings

from crmapconverter.opendriveparser.elements.road import Road

from commonroad.scenario.traffic_sign import (
    TrafficSign, TrafficLight, TrafficSignElement, TrafficSignIDZamunda, TrafficSignIDGermany, TrafficSignIDUsa, TrafficSignIDChina,
    TrafficSignIDSpain, TrafficSignIDRussia, TrafficLightDirection

)

def get_traffic_signals(road: Road):

    traffic_signs = []
    traffic_lights = []

    for signal in road.signals:

        position, tangent = road.planView.calc(signal.s)
        position = np.array([position[0] + signal.t * np.cos(tangent + 3.14159/2),
                             position[1] + signal.t * np.sin(tangent + 3.14159/2)])

        if signal.dynamic == 'no':

            if signal.subtype == '-1' or 'none':
                additional_values = []
            else:
                additional_values = list([signal.subtype])

            if signal.country == 'DEU':
                try:
                    element_id = TrafficSignIDGermany(signal.type)
                except ValueError:
                    warnings.warn("OpenDRIVE/traffic_signals.py: Unknown German traffic sign "
                                  "with ID {}!".format(signal.type))
                    element_id = TrafficSignIDGermany.UNKNOWN

            elif signal.country == 'USA':
                try:
                    element_id = TrafficSignIDUsa(signal.type)
                except ValueError:
                    warnings.warn("OpenDRIVE/traffic_signals.py: Unknown US traffic sign "
                                  "with ID {}!".format(signal.type))
                    element_id = TrafficSignIDUsa.UNKNOWN

            elif signal.country == 'CHN':
                try:
                    element_id = TrafficSignIDChina(signal.type)
                except ValueError:
                    warnings.warn("OpenDRIVE/traffic_signals.py: Unknown Chinese traffic sign "
                                  "with ID {}!".format(signal.type))
                    element_id = TrafficSignIDChina.UNKNOWN

            elif signal.country == 'ESP':
                try:
                    element_id = TrafficSignIDSpain(signal.type)
                except ValueError:
                    warnings.warn("OpenDRIVE/traffic_signals.py: Unknown Spanish traffic sign "
                                  "with ID {}!".format(signal.type))
                    element_id = TrafficSignIDSpain.UNKNOWN

            elif signal.country == 'RUS':
                try:
                    element_id = TrafficSignIDRussia(signal.type)
                except ValueError:
                    warnings.warn("OpenDRIVE/traffic_signals.py: Unknown Russian traffic sign "
                                  "with ID {}!".format(signal.type))
                    element_id = TrafficSignIDRussia.UNKNOWN

            else:
                try:
                    element_id = TrafficSignIDZamunda(signal.type)
                except ValueError:
                    warnings.warn("OpenDRIVE/traffic_signals.py: Unknown Zamunda traffic sign "
                                  "with ID {}!".format(signal.type))
                    element_id = TrafficSignIDZamunda.UNKNOWN

            traffic_sign_element = TrafficSignElement(
                traffic_sign_element_id=element_id,
                additional_values=additional_values
            )

            traffic_sign = TrafficSign(
                traffic_sign_id=signal.id + 1000,
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

                traffic_light = TrafficLight(
                    traffic_light_id=signal.id + 2000,
                    cycle=[],
                    position=position,
                    time_offset=0,
                    direction=TrafficLightDirection.ALL,
                    active=True
                )

            else:
                pass

            traffic_lights.append(traffic_light)

    return traffic_lights, traffic_signs
