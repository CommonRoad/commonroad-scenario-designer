

import xml.etree.ElementTree as ElTree
from ordered_set import OrderedSet
from src.scenario.scenario import Scenario
import src.scenario.obstacle as Obstacle
import utm
import src.scenario.traffic_sign as tS

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

    ways = root.iter('way')
    fairways = OrderedSet()
    coastlines = OrderedSet()

    for way in ways: #find fairways and coastlines in OSM
        for tag in way.iter('tag'):
            if tag.attrib['k'] == 'seamark:type' and tag.attrib['v'] == 'fairway':
                fairways.add(way)
                break
            if tag.attrib['k'] == 'natural' and tag.attrib['v'] == 'coastline':
                coastlines.add(way)
                break

    scenario = Scenario(1.0,2) #TODO:adjust timestep,id
    for buoy in buoys: #add buoyes to scenario
        lat = float(buoy.get('lat'))
        lon = float(buoy.get('lon'))
        coordinates = utm.from_latlon(lat,lon)
        type = tS.TrafficSignElementID(getType(buoy))
        element = tS.TrafficSignElement(type,[])
        sign = tS.TrafficSign(Scenario.generate_object_id(scenario),element,coordinates)
        scenario.add_objects(sign,[])


    for water in coastlines: #add coastlines to scenario
        boundarylist = []
        for nd in water.iter('nd'):
            xpath = "./node[@id='{index}']".format(index=nd.attrib['ref'])
            node = root.find(xpath)
            coordinates = utm.from_latlon(float(node.get('lat')),float(node.get('lon')))




def getType(buoy) -> str:
    """
    sorts the OSM buoy types to their equals in CommonOcean
    """

    for tag in buoy.iter('tag'):
        if str.find(tag.attrib['k'], 'seamark:buoy_cardinal:category'):
            if tag.attrib['v'] == 'north':
                return '104'
            elif tag.attrib['v'] == 'east':
                return '105'
            elif tag.attrib['v'] == 'south':
                return '106'
            elif tag.attrib['v'] == 'west':
                return '107'
        elif str.find(tag.attrib['k'], 'seamark:buoy_installation'):
            return '103'
        elif str.find(tag.attrib['k'], 'seamark:buoy_isolated_danger'):
            return '103'
        elif str.find(tag.attrib['k'], 'seamark:buoy_lateral:colour'):
            if tag.attrib['v'] == 'red':
                return '101'
            elif tag.attrib['v'] == 'green':
                return '102'
        elif str.find(tag.attrib['k'], 'seamark:buoy_safe_water'):
            return '103'
        elif str.find(tag.attrib['k'], 'seamark:buoy_special_purpose'):
            return '103'
    return '103'