from typing import Optional, Type, Union
from pyproj import CRS, Transformer
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
from crdesigner.common.config.lanelet2_config import lanelet2_config
from crdesigner.common.config.opendrive_config import open_drive_config

# Target orthometric CRS (ETRF89 + EVRF2007)
CRS_orthometric = CRS.from_epsg(7915)

# Lazily initialized global transformer for ellipsoidal -> orthometric conversion
_height_transformer: Optional[Transformer] = None


def init_height_transformer_from_georef(proj4_str: str) -> None:
    """Initialize height transformer using a proj4 string (from OpenDRIVE geoReference).

    Falls back to `lanelet2_config.height_geoid_proj4` if input is empty.
    """
    global _height_transformer
    # Honor global toggle: disable initialization when orthometric conversion is off
    if not getattr(open_drive_config, "enable_orthometric_height_conversion", True):
        _height_transformer = None
        return
    proj = (proj4_str or "").replace("\n", "").strip()
    if not proj:
        proj = lanelet2_config.height_geoid_proj4

    crs_ellipsoid = CRS.from_proj4(proj)
    _height_transformer = Transformer.from_crs(
        crs_ellipsoid, CRS_orthometric, always_xy=True
    )

def convert_height_ellipsoid_to_orthometric(x: float, y: float, z_ellipsoid: float) -> float:
    """Convert height from ellipsoid to orthometric.

    :param x: x coordinate.
    :param y: y coordinate.
    :param z: height above ellipsoid.
    :return: height above orthometric.
    """
    # Fast path: if disabled, just return the input ellipsoidal height unchanged
    if not getattr(open_drive_config, "enable_orthometric_height_conversion", True):
        return z_ellipsoid

    # Initialize transformer on first use if not already done, using default config.
    global _height_transformer
    if _height_transformer is None:
        init_height_transformer_from_georef(lanelet2_config.height_geoid_proj4)

    try:
        _, _, z_orthometric = _height_transformer.transform(x, y, z_ellipsoid)
        return z_orthometric
    except Exception:
        # Fallback to original height on any failure
        return z_ellipsoid

        

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
