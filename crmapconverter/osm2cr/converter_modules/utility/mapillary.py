"""
This module is used to retrieve a Mapillary data from the Mapillary open API.
An Internet connection is needed and a valid Mapillary ClinetID has to be provided in the config.py file
"""

import json
from urllib.request import urlopen
from urllib.error import URLError
from crmapconverter.osm2cr import config
import enum
import numpy as np
from dataclasses import dataclass

from crmapconverter.osm2cr.converter_modules.graph_operations import road_graph as rg
from crmapconverter.osm2cr.converter_modules.utility.geometry import lon_lat_to_cartesian


@dataclass
class Bbox:
    west: float
    south: float
    east: float
    north: float

def get_mappilary_traffic_signs(bbox):
    """
    Retrive traffic signs found with Mapillary in a given bounding box

    :param1 bbox: Bounding box
    :return: listof traffic signs with lat,lng position
    """


    # try to request information for the given scenario center
    try:
        if config.MAPILLARY_CLIENT_ID == 'demo':
            raise ValueError('mapillary demo ID used')

        query = "https://a.mapillary.com/v3/map_features?layers=trafficsigns&bbox={},{},{},{}&per_page=1000&client_id={}".format(
            bbox.west, bbox.south, bbox.east, bbox.north, config.MAPILLARY_CLIENT_ID)
        data = urlopen(query).read().decode('utf-8')
        response = json.loads(data)

        #print(response)

        feature_list = response['features']
        # for feature in feature_list:
        #     print(feature[ 'properties']['value'], feature['geometry']['coordinates'])
        # sign consists out of value, coordinates in lat_lng, direction in degrees [0, 360]
        signs = [[feature['properties']['value'], feature['geometry']['coordinates'], feature['properties']['direction']] for feature in feature_list]

        # map signs to commonroad format traffic_signs / utm32
        #commonroad_signs = list(map())
        #print(signs)
        return signs
    except ValueError:
        print("Mapillary Device ID is not set.")
        return None


def add_mapillary_signs_to_graph(graph:rg.Graph):
    """
    Add Mapillary sings to the road graph

    :param1 graph: Road graph
    :return: None
    """

    # graph bounds are not ordered as mapillary API expects it
    bbox = Bbox(graph.bounds[1],graph.bounds[2],graph.bounds[3],graph.bounds[0])
    #print("bbox")
    #print(bbox)
    signs = get_mappilary_traffic_signs(bbox)
    # convert lat lng to cartestian
    #signs = [(sign[0], lon_lat_to_cartesian(np.asarray(sign[1]), graph.center_point)) for sign in signs]
    # faulty signs = list(map(lambda y: lon_lat_to_cartesian(y[1], graph.center_point), signs))
    # print(signs)
    if signs is not None:
        for sign in signs:
            #node = graph.find_closest_node_by_lat_lng(sign[1])
            #traffic_sign = rg.GraphTrafficSign({'traffic_sign': 'DE:114'}, node)
            # find edge
            edge = graph.find_closest_edge_by_lat_lng(sign[1])
            # add to graph traffic signs
            traffic_sign = rg.GraphTrafficSign({'mapillary': sign[0]}, node=None, edges=[[edge]], direction=sign[2]) # TODO virutal
            graph.traffic_signs.append(traffic_sign)


if __name__ == "__main__":

    # example
    bbox = Bbox(12.8873,55.4913,13.1561,55.658)
    # dachauer/pelkovenstr
    bbox= Bbox(11.510614,48.180581,11.513178,48.181719)
    get_mappilary_traffic_signs(bbox)