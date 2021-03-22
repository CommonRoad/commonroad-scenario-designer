

import xml.etree.ElementTree as ElTree
from ordered_set import OrderedSet
from src.scenario.scenario import Scenario
import src.scenario.obstacle as Obstacle
import utm
import src.scenario.traffic_sign as tS
import src.scenario.waters as w
import numpy as np
#import commonroad.scenario.lanelet as c

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
    for buoy in buoys: #add buoyes to scenario as TrafficSigns
        lat = float(buoy.get('lat'))
        lon = float(buoy.get('lon'))
        coordinates = utm.from_latlon(lat,lon) #TODO: convert to one field
        type = tS.TrafficSignElementID(getType(buoy))
        element = tS.TrafficSignElement(type,[])
        sign = tS.TrafficSign(Scenario.generate_object_id(scenario),element,coordinates)
        scenario.add_objects(sign,[])

    if len(coastlines) > 0:
        addLand(coastlines,scenario, root)
    if len(fairways) > 0:
        addWaters(fairways, scenario, w.WatersType('trafficseparationzone'), root)





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

def addWaters(waters, scenario: Scenario, type: w.WatersType, root):
    for water in waters:  # add waters to scenario
        z=[]
        for nd in water.iter('nd'):
            #get coordinates for point
            xpath = "./node[@id='{index}']".format(index=nd.attrib['ref'])
            node = root.find(xpath)
            coordinates = utm.from_latlon(float(node.get('lat')), float(node.get('lon')))
            z.append([coordinates[0], coordinates[1]])

        if(len(x)>4):
            center_v = np.array([[1, 2], [2, 3]])  # TODO: find good center_vertices
            water2 = w.Waters(np.array([z[1], z[0]]), center_v, np.array(z[2:]), Scenario.generate_object_id(scenario),
                              None, None, {type})
            scenario.add_objects(water2, [])

def addLand(lands, scenario: Scenario, root):
    for land in lands:  # add waters to scenario
        z=[]
        for nd in land.iter('nd'):
            #get coordinates for point
            xpath = "./node[@id='{index}']".format(index=nd.attrib['ref'])
            node = root.find(xpath)
            coordinates = utm.from_latlon(float(node.get('lat')), float(node.get('lon')))
            z.append([coordinates[0],coordinates[1]])
            #TODO: bring coordinates to one field in UTM


        if(len(x)>4):
            center_v = np.array([[1,2],[2,3]]) #TODO: find good center_vertices
            water2 = w.Waters(np.array([z[1],z[0]]),center_v,np.array(z[2:]), Scenario.generate_object_id(scenario),None,None,{w.WatersType('water')})
            scenario.add_objects(water2,[])