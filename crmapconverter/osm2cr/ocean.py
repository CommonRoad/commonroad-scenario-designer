

import xml.etree.ElementTree as ElTree
from ordered_set import OrderedSet
from commonocean_io.src.scenario.scenario import Scenario
import commonocean_io.src.scenario.obstacle as Obstacle
from commonroad.geometry.shape import Circle
import utm
import commonocean_io.src.scenario.traffic_sign as tS

def convert_seamap(filename):
    """

    finds Buoys in OSM and converts them to a CommonOcean scenario

    """
    tree = ElTree.parse(filename)
    root = tree.getroot()
    nodes = root.iter('node')
    buoys =  OrderedSet()

    for node in nodes: #finds buoys in OSM
        for tag in node.iter('tag'):
            if str.find(tag.attrib['k'], 'seamark:buoy'):
                    buoys.add(node)
            break

    scenario = Scenario(1.0,2) #TODO:adjust timestep,id
    id = 0
    for buoy in buoys:
        lat = float(buoy.get('lat'))
        lon = float(buoy.get('lon'))
        coordinates = utm.from_latlon(lat,lon)
        type = tS.TrafficSignElementID('101')
        element = tS.TrafficSignElement(type,[])
        sign = tS.TrafficSign(id,element,coordinates)
        id += 1