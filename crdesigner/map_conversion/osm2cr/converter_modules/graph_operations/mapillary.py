"""
This module is used to retrieve a Mapillary data from the Mapillary open API.
An Internet connection is needed and a valid Mapillary ClinetID has to be provided in the osm_config.py file
"""

import json
from urllib.error import URLError
from urllib.request import urlopen

from crdesigner.common.config.osm_config import osm_config as config
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations.road_graph._graph import (
    Graph,
)
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations.road_graph._graph_traffic_sign import (
    GraphTrafficSign,
)


class Bbox:
    """
    Helper class for Bbox representation
    """

    west: float
    south: float
    east: float
    north: float

    def __init__(self, west: float, south: float, east: float, north: float):
        self.west = west
        self.south = south
        self.east = east
        self.north = north


def get_mappilary_traffic_signs(bbox: Bbox):
    """
    Retrieve traffic signs found with Mapillary in a given bounding box.
    Mapillary key needs to be provided in config file

    :param1 bbox: Bounding box
    :return: list of traffic signs with lat,lng position
    """

    # try to request information for the given scenario center
    try:
        if config.MAPILLARY_CLIENT_ID == "demo":
            raise ValueError("mapillary demo ID used")

        query = (
            "https://a.mapillary.com/v3/map_features?layers=trafficsigns&bbox={},{},{},{}&per_page=1000&client_id"
            "={}".format(bbox.west, bbox.south, bbox.east, bbox.north, config.MAPILLARY_CLIENT_ID)
        )
        data = urlopen(query).read().decode("utf-8")
        response = json.loads(data)

        feature_list = response["features"]
        signs = [
            [
                feature["properties"]["value"],
                feature["geometry"]["coordinates"],
                feature["properties"]["direction"],
            ]
            for feature in feature_list
        ]
        return signs

    except ValueError:
        print("mapillary Device ID is not set")
        return None
    except URLError:
        print("error while connecting to mapillary servers. Skipping Mapillary signs")
        return None


def add_mapillary_signs_to_graph(graph: Graph):
    """
    Add Mapillary sings to the road graph

    :param1 graph: Road graph
    :return: None
    """

    # graph bounds are not ordered as mapillary API expects it and need to be rearranged
    bbox = Bbox(
        graph.bounds.lon_min, graph.bounds.lat_min, graph.bounds.lon_max, graph.bounds.lat_max
    )
    # retrieve traffic signs from given bbox
    signs = get_mappilary_traffic_signs(bbox)
    if signs is not None:
        for sign in signs:
            edge = graph.find_closest_edge_by_lat_lng(sign[1], direction=sign[2])
            # add to graph traffic signs
            traffic_sign = GraphTrafficSign(
                {"mapillary": sign[0]}, node=None, edges=[[edge]], direction=sign[2]
            )  # TODO virutal
            graph.traffic_signs.append(traffic_sign)
