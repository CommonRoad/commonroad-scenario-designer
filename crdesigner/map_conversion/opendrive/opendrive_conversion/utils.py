import iso3166
from dataclasses import dataclass
from typing import Union
from commonroad.scenario.traffic_sign import TrafficSignIDZamunda, TrafficSignIDGermany, TrafficSignIDUsa, \
    TrafficSignIDChina, TrafficSignIDSpain, TrafficSignIDRussia, TrafficSignIDArgentina, TrafficSignIDBelgium, \
    TrafficSignIDFrance, TrafficSignIDGreece, TrafficSignIDCroatia, TrafficSignIDItaly, TrafficSignIDPuertoRico


def encode_road_section_lane_width_id(road_id, section_id, lane_id, width_id) -> str:
    """Encodes a road section lane width with an ID.

    :param road_id: ID of road.
    :type road_id: int
    :param section_id: ID of RoadSection.
    :type section_id: int
    :param lane_id: ID of Lane.
    :type lane_id: int
    :param width_id: ID of LaneWidth.
    :type width_id: int
    :return: A new ID concatenated from the input IDs.
    :rtype: str
    """
    return ".".join([str(road_id), str(section_id), str(lane_id), str(width_id)])

def encode_mark_lane_width_id(roadId, sectionId, laneId, widthId, mId) -> str:
    """Encodes a road section lane width with an ID.

    :param roadId: ID of road.
    :type roadId: int
    :param sectionId: ID of RoadSection.
    :type sectionId: int
    :param laneId: ID of Lane.
    :type laneId: int
    :param widthId: ID of LaneWidth.
    :type widthId: int
    :return: A new ID concatenated from the input IDs.
    :rtype: str
    """
    return ".".join([str(roadId), str(sectionId), str(laneId), str(widthId), str(mId)])


def get_signal_country(signal_country: str) -> str:
    """
    ISO3166 standard to find three-letter country id
    :param signal_country: String value of the country.
    :type signal_country: str
    :return: The 3-letter country ID per ISO3166.
    :rtype: str
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


def get_traffic_sign_enum_from_country(country: str) -> Union[TrafficSignIDZamunda, TrafficSignIDGermany,
                                                              TrafficSignIDUsa, TrafficSignIDChina, TrafficSignIDSpain,
                                                              TrafficSignIDRussia, TrafficSignIDArgentina,
                                                              TrafficSignIDBelgium, TrafficSignIDFrance,
                                                              TrafficSignIDGreece, TrafficSignIDCroatia,
                                                              TrafficSignIDItaly, TrafficSignIDPuertoRico]:
    """Returns the traffic sign ID enumeration for the country supplied by the ISO3166 country string.

    :param country: ISO3166 country string to get the traffic sign enumeration from.
    :type country: str
    :return: The enumeration of the country if it is supported, else the Zamunda enumeration.
    :rtype: Union
    """
    if country == "DEU":
        return TrafficSignIDGermany
    elif country == "USA":
        return TrafficSignIDUsa
    elif country == "CHN":
        return TrafficSignIDChina
    elif country == "ESP":
        return TrafficSignIDSpain
    elif country == "RUS":
        return TrafficSignIDRussia
    elif country == "ARG":
        return TrafficSignIDArgentina
    elif country == "BEL":
        return TrafficSignIDBelgium
    elif country == "FRA":
        return TrafficSignIDFrance
    elif country == "GRC":
        return TrafficSignIDGreece
    elif country == "HRV":
        return TrafficSignIDCroatia
    elif country == "ITA":
        return TrafficSignIDItaly
    elif country == "PRI":
        return TrafficSignIDPuertoRico
    else:
        return TrafficSignIDZamunda
