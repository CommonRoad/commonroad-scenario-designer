# -*- coding: utf-8 -*-

from crmapconverter.opendriveparser.elements.opendrive import OpenDrive
from crmapconverter.opendriveparser.elements.roadSignal import Signal
from commonroad.scenario import traffic_sign as trf
from commonroad.scenario.scenario import Scenario

"create traffic signs and traffic lights"
def judge_type(opendrive:OpenDrive):

    for road in opendrive.roads:

        if len(road.signals) != 0:

            for signal in road.signals:

                if signal.dynamic == 'yes':
                    extract_traffic_sign_info(signal)
                elif signal.dynamic == 'no':
                    extract_traffic_light_info(signal)

    return None

def extract_traffic_sign_info(signal: Signal):

    """take opendrive -> roads -> road -> signals -> static signals as traffic signs"""

    if trf.SupportedTrafficSignCountry(signal.country) not in trf.SupportedTrafficSignCountry:

        print("Country not supported, use default instead")

    elif trf.SupportedTrafficSignCountry(signal.country) in trf.SupportedTrafficSignCountry:

        pass

    traffic_sign_element = trf.TrafficSignELement(
        traffic_sign_element_id = signal.type,
        additional_values = list([signal.subtype])
    )

    new_sign = trf.TrafficSign(
        traffic_sign_id = signal.id
        traffic_sign_elements = list([traffic_sign_element]),
        #TODO: Calculate the lanelet where to put the sign
        first_occurrence =  None,
        #TODO：Calculate the position
        position = [],
        virtual = False
    )


    return None
    


def extract_traffic_light_info(opendrive:OpenDrive):



    return None
