

import xml.etree.ElementTree as ElTree
from ordered_set import OrderedSet
from commonocean_io.src.scenario.scenario import Scenario
import commonocean_io.src.scenario.obstacle as Obstacle
from commonroad.geometry.shape import Circle

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
    for buoy in buoys: #TODO: adjust position
        c = Circle(1)
        #scenario.add_objects(Obstacle.StaticObstacle(id, Obstacle.ObstacleType.BUOY,c, Obstacle.State(position=c,orientation=0)))
        id += 1