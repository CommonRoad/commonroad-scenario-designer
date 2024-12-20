from typing import Type, Union

import iso3166
from commonroad.scenario.traffic_sign import (
    TrafficSignIDArgentina,
    TrafficSignIDBelgium,
    TrafficSignIDChina,
    TrafficSignIDCroatia,
    TrafficSignIDFrance,
    TrafficSignIDGermany,
    TrafficSignIDGreece,
    TrafficSignIDItaly,
    TrafficSignIDPuertoRico,
    TrafficSignIDRussia,
    TrafficSignIDSpain,
    TrafficSignIDUsa,
    TrafficSignIDZamunda,
)


def encode_road_section_lane_width_id(
    road_id: int, section_id: int, lane_id: int, width_id: int
) -> str:
    """Encodes a road section lane width with an ID.

    :param road_id: ID of road.
    :param section_id: ID of RoadSection.
    :param lane_id: ID of Lane.
    :param width_id: ID of LaneWidth.
    :return: A new ID concatenated from the input IDs.
    """
    return ".".join([str(road_id), str(section_id), str(lane_id), str(width_id)])


def encode_mark_lane_width_id(
    road_id: int, section_id: int, lane_id: int, width_id: int, m_id: int
) -> str:
    """Encodes a road section lane width with an ID.

    :param road_id: ID of road.
    :param section_id: ID of RoadSection.
    :param lane_id: ID of Lane.
    :param width_id: ID of LaneWidth.
    :param m_id: ID of lane marking.
    :return: A new ID concatenated from the input IDs.
    """
    return ".".join([str(road_id), str(section_id), str(lane_id), str(width_id), str(m_id)])


def get_signal_country(signal_country: str) -> str:
    """
    ISO3166 standard to find three-letter country id

    :param signal_country: String value of the country.
    :return: The 3-letter country ID per ISO3166.
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


def get_traffic_sign_enum_from_country(
    country: str,
) -> Union[
    Type[TrafficSignIDZamunda],
    Type[TrafficSignIDGermany],
    Type[TrafficSignIDUsa],
    Type[TrafficSignIDChina],
    Type[TrafficSignIDSpain],
    Type[TrafficSignIDRussia],
    Type[TrafficSignIDArgentina],
    Type[TrafficSignIDBelgium],
    Type[TrafficSignIDFrance],
    Type[TrafficSignIDGreece],
    Type[TrafficSignIDCroatia],
    Type[TrafficSignIDItaly],
    Type[TrafficSignIDPuertoRico],
]:
    """Returns the traffic sign ID enumeration for the country supplied by the ISO3166 country string.

    :param country: ISO3166 country string to get the traffic sign enumeration from.
    :return: The enumeration of the country if it is supported, else the Zamunda enumeration.
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
