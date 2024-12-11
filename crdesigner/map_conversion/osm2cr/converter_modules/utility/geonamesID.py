"""
This module is used to retrieve a geonamesID for a given coordinate.
An Internet connection is needed and a valid geonames username has to be provided in the osm_config.py file
"""

import json
import logging
from urllib.error import URLError
from urllib.request import urlopen

import kdtree

from crdesigner.common.config.osm_config import osm_config as config
from crdesigner.map_conversion.osm2cr.converter_modules.utility.labeling_create_tree import (
    find_nearest_neighbor,
)


def get_geonamesID(lat: float, lng: float, cities_kdtree: kdtree.KDNode = None) -> int:
    """
    Retrieve a geonamesID for a given scenario coordinate center

    :param1 lat: Latitude of scenario center
    :param2 lng: Longitude of scenario center
    :param3 cities_kdtree: None → use API, kdtree.KDNode → use offline implementation
    :return: GeonamesID for scenario
    """
    # try to request information for the given scenario center
    try:
        if cities_kdtree is not None:
            return find_nearest_neighbor(cities_kdtree, (lat, lng)).geonameID
        else:
            if config.GEONAMES_USERNAME == "demo":
                raise ValueError("geonames demo ID used")

            query = (
                "http://api.geonames.org/findNearbyPlaceNameJSON?lat={}&lng={}&username={}".format(
                    lat, lng, config.GEONAMES_USERNAME
                )
            )
            data = urlopen(query).read().decode("utf-8")
            response = json.loads(data)

            # choose the first entry's geonameID to get the closest location
            code = response["geonames"][0]["geonameId"]

            return code

    # catch connection error
    except ValueError:
        logging.error("Fallback GeonamesID used.")
        return -999
    except URLError:
        logging.error(
            "No Internet connection could be established for retrieving a GeonamesID. "
            "Using fallback GeonamesID instead."
        )
        return -999
    # catch account errors
    except KeyError:
        try:
            logging.error(
                "Couldn't retrieve a valid GeonamesID. Using fallback GeonamesID instead. "
                "Message from Geonames server: " + response["status"]["message"]
            )
        except KeyError:
            logging.error(
                "Couldn't retrieve a valid GeonamesID. Using fallback GeonamesID instead."
            )
        return -999
    # catch errors we don't know about yet
    except Exception:
        logging.error("Couldn't retrieve a GeonamesID. Using fallback GeonamesID instead.")
        return -999
