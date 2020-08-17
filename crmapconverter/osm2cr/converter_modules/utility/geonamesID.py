"""
This module provides is used to retrieve a geonames ID for a given coordinate.
An Internet connection is needed and a valid geonames user name has to be provided in the config.py file
"""

import json
import traceback

from urllib.request import urlopen
from urllib.error import URLError
from crmapconverter.osm2cr import config


def get_geonamesID(lat: float, lng: float):
    """
    Retrive specific location to extract intersections from based on coordinate bounding box

    :param1 lat: Latitude of scenario center
    :param2 lng: Longitude of scenario center
    :return: GeonamesID for scenario
    """


    # try to request information for the given scenario center
    try:
        query = "http://api.geonames.org/findNearbyPlaceNameJSON?lat={}&lng={}&username={}".format(
            lat, lng, config.GEONAMES_USERNAME
        )
        data = urlopen(query).read().decode('utf-8')
        response = json.loads(data)

        # choose the first entry's geonameID to get the closest location
        code = response['geonames'][0]['geonameId']

        return code

    except URLError:
        print('No Internet connection could be established. Using fallback GeonamesID')
        return -999
    except KeyError:
        try:
            print("message from Geonames server: " + response['status']['message'])
        except KeyError:
            print("Error retrieving a valid GeonamesID. Using fallback GeonamesID")
        return -999
    except Exception:
        print("Couldn't retrieve a GeonamesID")
        return -999
