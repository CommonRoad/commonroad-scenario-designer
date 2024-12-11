"""
This module provides methods to download OSM maps within the application.
"""

import xml.etree.ElementTree
from typing import Tuple
from urllib.request import urlopen

import numpy as np

from crdesigner.common.config.osm_config import osm_config as config


def write_bounds_to_file(filename: str, lon1: float, lat1: float, lon2: float, lat2: float):
    """
    adds a tag to the downloaded osm file which defines the bounds of the downloaded window
    this is used in osm_parser.py to only extract points within these bounds
    tag: <custom_bounds lon1='12.34' lon2='12.34' lat1='12.34' lat2='12.34' </custom_bounds>

    :param filename:
    :param lon1:
    :param lat1:
    :param lon2:
    :param lat2:
    :return:
    """
    tree = xml.etree.ElementTree.parse(filename)

    tag = xml.etree.ElementTree.SubElement(tree.getroot(), "custom_bounds")
    tag.attrib["lon1"] = str(lon1)
    tag.attrib["lon2"] = str(lon2)
    tag.attrib["lat1"] = str(lat1)
    tag.attrib["lat2"] = str(lat2)

    tree.write(filename, encoding="utf-8", xml_declaration=True)


def download_map(filename: str, lon1: float, lat1: float, lon2: float, lat2: float):
    """
    downloads an osm map of a specified area and saves it to disk

    :param filename: name of the file the map is saved to
    :param lon1: longitude of the left border of the downloaded area
    :param lat1: latitude of the upper border of the downloaded area
    :param lon2: longitude of the right border of the downloaded area
    :param lat2: latitude of the lower border of the downloaded area
    """
    # query = "https://overpass-api.de/api/map?bbox={},{},{},{}".format(
    #     lon1, lat1, lon2, lat2
    # )
    query = "https://api.openstreetmap.org/api/0.6/map?bbox={},{},{},{}".format(
        lon1, lat1, lon2, lat2
    )
    print("downloading map")
    data = urlopen(query).read()
    with open(filename, "wb") as file:
        file.write(data)
    print("writing custom bounds")
    write_bounds_to_file(filename, lon1, lat1, lon2, lat2)


def get_frame(lon: float, lat: float, radius: float) -> Tuple[float, float, float, float]:
    """
    gets the frame of area to download

    :param lon: longitude of center of the area
    :param lat: latitude of center of the area
    :param radius: half width of the frame
    :return: frame of the area
    """
    lon_constant = np.pi / 180 * config.EARTH_RADIUS * np.cos(np.radians(lat))
    lat_constant = np.pi / 180 * config.EARTH_RADIUS
    lon1 = lon - radius / lon_constant
    lat1 = lat - radius / lat_constant
    lon2 = lon + radius / lon_constant
    lat2 = lat + radius / lat_constant
    return lon1, lat1, lon2, lat2


def download_around_map(filename: str, lat: float, lon: float, radius: float = 500):
    """
    downloads map around center point and saves it to file

    :param filename: name of the file the map is saved to
    :param lon: longitude of center of the area
    :param lat: latitude of center of the area
    :param radius: half width of the frame
    """
    lon1, lat1, lon2, lat2 = get_frame(lon, lat, radius)
    download_map(config.SAVE_PATH + filename, lon1, lat1, lon2, lat2)
