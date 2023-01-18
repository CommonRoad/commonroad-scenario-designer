from collections import defaultdict
from typing import List, Tuple
from shapely.geometry import LineString
import numpy as np
from pyproj import Proj
import unittest
import os
from lxml import etree
from typing import Optional
import io
import sys

from commonroad.scenario.lanelet import StopLine, LineMarking, RoadUser, Lanelet, LaneletNetwork
from commonroad.scenario.traffic_sign import TrafficSignIDGermany, TrafficSignElement
from commonroad.scenario.scenario import Scenario, ScenarioID, TrafficSign, Location
from crdesigner.map_conversion.lanelet2.lanelet2cr import Lanelet2CRConverter, _add_closest_traffic_sign_to_lanelet, _add_stop_line_to_lanelet
from crdesigner.map_conversion.common.utils import generate_unique_id
from crdesigner.map_conversion.opendrive.opendrive_conversion.conversion_lanelet import ConversionLanelet
from crdesigner.map_conversion.lanelet2.lanelet2_parser import Lanelet2Parser
from crdesigner.map_conversion.lanelet2.lanelet2cr import Lanelet2CRConverter, _two_vertices_coincide
from crdesigner.map_conversion.opendrive.opendrive_conversion.conversion_lanelet_network import ConversionLaneletNetwork
from crdesigner.map_conversion.lanelet2.lanelet2 import OSMLanelet, WayRelation, DEFAULT_PROJ_STRING, Node, Way, RightOfWayRelation
from crdesigner.map_conversion.osm2cr.converter_modules.utility.geometry import (
    point_to_line_distance,
    distance as point_to_polyline_distance
)
from crdesigner.configurations.get_configs import get_configs

NODE_DISTANCE_TOLERANCE = 0.01  # this is in meters
PRIORITY_SIGNS = [TrafficSignIDGermany.PRIORITY, TrafficSignIDGermany.RIGHT_OF_WAY]
# removed TrafficSignIDGermany.RIGHT_BEFORE_LEFT

ADJACENT_WAY_DISTANCE_TOLERANCE = 0.05

with open(f"{os.path.dirname(os.path.realpath(__file__))}/../test_maps/lanelet2/traffic_speed_limit_utm.osm") as fh:
            osm = Lanelet2Parser(etree.parse(fh).getroot()).parse()

def contains(list, filter):
    for x in list:
        if filter(x):
            return True
    return False

class TestLanelet2CRConverter(unittest.TestCase):
    def test_init(self):
        l2cr = Lanelet2CRConverter()
        #testing the initialization values without opening the scenario
        self.assertIsNone(l2cr._left_way_ids) 
        self.assertIsNone(l2cr._right_way_ids) 
        self.assertIsNone(l2cr.first_left_pts) 
        self.assertIsNone(l2cr.last_left_pts)
        self.assertIsNone(l2cr.first_right_pts) 
        self.assertIsNone(l2cr.last_right_pts) 
        self.assertIsNone(l2cr.osm)
        self.assertIsNone(l2cr.lanelet_network)
        self.assertIsNone(l2cr.origin_utm) 

        #testing the default proj
        self.assertEqual(l2cr.proj,Proj("+proj=utm +zone=32 +ellps=WGS84"))
    
    def test_custom_proj_string_init(self):
        custom_proj_string = "+proj=utm +zone=59 +south"
        l2cr = Lanelet2CRConverter(custom_proj_string)
        self.assertEqual(l2cr.proj,Proj(custom_proj_string))

    def test_call(self):
        l2cr = Lanelet2CRConverter() #object refered to as "self" in the source code
        scenario = l2cr(osm)

        #test if the osm is the same as the imported one
        self.assertEqual(l2cr.osm,osm)
        
        #test the use of a random node as an origin
        origin = next(iter(l2cr.osm.nodes.values()))
        self.assertEqual(l2cr.origin_utm,l2cr.proj(origin.lon,origin.lat))
        
        #test the default scenario_id
        self.assertEqual(scenario.scenario_id.country_id,"ZAM")
        self.assertEqual(scenario.scenario_id.map_name,"OpenDrive")
        self.assertEqual(scenario.scenario_id.map_id,123)

        #test the scenario values given in the constructor
        self.assertEqual(scenario.dt,0.1)
        self.assertEqual(scenario.location,Location(gps_latitude=origin.lat,gps_longitude=origin.lon))
        
        #test the class of the lanelet network
        self.assertEqual(l2cr.lanelet_network.__class__,LaneletNetwork)
        
        #test if the lanelet networks are equal
        self.assertEqual(scenario.lanelet_network,l2cr.lanelet_network)
    
    def test__add_closest_traffic_sign_to_lanelet(self):
        #testing the function by creating a list of lanelets and a list of signs and checking the result

        #lanelet1
        right_vertices = np.array([[0, 0], [1, 0], [2, 0]])
        left_vertices = np.array([[0, 1], [1, 1], [2, 1]])
        center_vertices = np.array([[0, .5], [1, .5], [2, .5]])
        lanelet1 = Lanelet(left_vertices, center_vertices, right_vertices, 1)

        #lanelet2
        left_vertices2 = np.array([[10, 0], [11, 0], [12, 0]]) 
        right_vertices2 = np.array([[10, 1], [11, 1], [12, 1]])
        center_vertices2 = np.array([[10, 0.5], [11, 0.5], [12, 0.5]])
        lanelet2 = Lanelet(left_vertices2, center_vertices2, right_vertices2, 2)

        sign1 = TrafficSign(1,[],[],np.array([[3, 0], [3, 0]]),False) #should be closest to lanelet1
        sign2 = TrafficSign(2,[],[],np.array([[15, 0], [15, 0]]),False) #should be closest to lanelet2
        sign3 = TrafficSign(3,[],[],np.array([[4, 0], [4, 0]]),False) #should be closest to lanelet1, but the sign 1 is more closer, so this won't be added.

        #adding lanelets and signs to the list, as that is the format of input
        listlanelet = [lanelet1,lanelet2]
        listsign = [sign1,sign2,sign3]

        #calling the function
        returnedSigns = _add_closest_traffic_sign_to_lanelet(listlanelet,listsign)
        
        #testing the signs assigned to lanelets
        self.assertEqual(lanelet1.traffic_signs,{1})
        self.assertEqual(lanelet2.traffic_signs,{2})

        #testing the return value of the function
        for i in returnedSigns:
            if(i.traffic_sign_id==1):
                self.assertEqual(i,sign1)
            if(i.traffic_sign_id==2):
                self.assertEqual(i,sign2)   


    def test__add_stop_line_to_lanelet(self):
        #lanelet1
        right_vertices = np.array([[0, 0], [1, 0], [2, 0]])
        left_vertices = np.array([[0, 1], [1, 1], [2, 1]])
        center_vertices = np.array([[0, .5], [1, .5], [2, .5]])
        lanelet1 = Lanelet(left_vertices, center_vertices, right_vertices, 1)

        #lanelet2
        left_vertices2 = np.array([[10, 0], [11, 0], [12, 0]]) 
        right_vertices2 = np.array([[10, 1], [11, 1], [12, 1]])
        center_vertices2 = np.array([[10, 0.5], [11, 0.5], [12, 0.5]])
        lanelet2 = Lanelet(left_vertices2, center_vertices2, right_vertices2, 2)

        #stopLine that should not be reffered to any of the lanelets
        left_point = np.array([5,1])
        right_point = np.array([5,0])
        stopLine = StopLine(left_point,right_point,LineMarking.DASHED)
        _add_stop_line_to_lanelet([lanelet1,lanelet2],[stopLine])
        self.assertFalse(lanelet1.stop_line) #none is read as false
        self.assertFalse(lanelet2.stop_line) #none is read as false

        #stopLine that should be reffered to lanelet1
        left_point = np.array([2,1])
        right_point = np.array([2,0])
        stopLine = StopLine(left_point,right_point,LineMarking.DASHED)
        _add_stop_line_to_lanelet([lanelet1,lanelet2],[stopLine])
        self.assertCountEqual(lanelet1.stop_line.start,[2,1])
        self.assertCountEqual(lanelet1.stop_line.end,[2,0])
        
        #stopLine that should be reffered to lanelet2
        left_point = np.array([11,1])
        right_point = np.array([11,0])
        stopLine = StopLine(left_point,right_point,LineMarking.DASHED)
        _add_stop_line_to_lanelet([lanelet1,lanelet2],[stopLine])
        self.assertCountEqual(lanelet2.stop_line.start,[11,1])
        self.assertCountEqual(lanelet2.stop_line.end,[11,0])

    def test__right_of_way_to_traffic_sign(self):
        l2cr = Lanelet2CRConverter() #object refered to as "self" in the source code
        l2cr(osm)

        right_of_way_relation = list(osm.right_of_way_relations.values())[-1] #declaring our right_of_way_relation used for this testing
        serialized_element = right_of_way_relation.serialize_to_xml()

        #map of the generated id's for the lanelet CR format. Copied from the source code as there are problems generating the code. 
        map = {'-1775219': 1, '-1775268': 2, '-1775303': 3, '-1775308': 4, '-1775222': 5, '-1775263': 6, '-1775273': 7, '-1775283': 8, '-1775451': 9, '-1775227': 10, '-1775232': 11, '-1775298': 12, '-1775431': 13, '-1775238': 14, '-1775278': 15, '-1775288': 16,'-1775240': 17, '-1775426': 18, '-1775293': 19, '-1775247': 20, '-1775253': 21, '-1775248': 22, '-1775441': 23, '-1775258': 24, '-1775446': 25, '-1775436':26,'-1775219': 31, '-1775268': 32, '-1775303': 33, '-1775308': 34, '-1775222': 35, '-1775263': 36, '-1775273': 37, '-1775283': 38, '-1775451': 39, '-1775227': 40, '-1775232': 41, '-1775298': 42, '-1775431': 43, '-1775238': 44, '-1775278': 45, '-1775288': 46, '-1775240': 47, '-1775426': 48, '-1775293': 49, '-1775247': 50, '-1775253': 51, '-1775248': 52, '-1775441': 53, '-1775258': 54, '-1775446': 55, '-1775436': 56}
    
        #calling the function and getting the parameters that we will test
        yield_signs, priority_signs, yield_lanelets, priority_lanelets, stop_lines = l2cr._right_of_way_to_traffic_sign(right_of_way_relation,map)
        #getting the way signs from the osm to compare them with the CR signs

        traffic_sign_ways = [l2cr.osm.find_way_by_id(r) for r in right_of_way_relation.refers]
        signs = yield_signs+priority_signs
        for traffic_sign_way in traffic_sign_ways:
            #getting the positions of the way
            traffic_sign_node = osm.find_node_by_id(traffic_sign_way.nodes[0])
            x, y = l2cr.proj(float(traffic_sign_node.lon), float(traffic_sign_node.lat))
            x -= l2cr.origin_utm[0]
            y -= l2cr.origin_utm[1]
            for sign in signs:
                #comparing the position so we know that those are the 2 same signs 
                if sign.position[0] == x and sign.position[1]==y: 
                    #reformatting the priority to fit the cr format
                    if traffic_sign_way.tag_dict.get("subtype") == "de206":
                        traffic_sign_type = TrafficSignIDGermany.STOP
                    elif traffic_sign_way.tag_dict.get("subtype") == "de102":
                        traffic_sign_type = TrafficSignIDGermany.RIGHT_BEFORE_LEFT
                    elif traffic_sign_way.tag_dict.get("subtype") == "de205":
                        traffic_sign_type = TrafficSignIDGermany.YIELD
                    elif traffic_sign_way.tag_dict.get("subtype") == "de301" or traffic_sign_way.tag_dict.get("subtype") =='right_of_way':
                        traffic_sign_type = TrafficSignIDGermany.RIGHT_OF_WAY
                    elif traffic_sign_way.tag_dict.get("subtype") == "de306":
                        traffic_sign_type = TrafficSignIDGermany.PRIORITY
                    else:
                        raise NotImplementedError(f"Lanelet type {traffic_sign_way.tag_dict['subtype']} not implemented")
                    self.assertEqual(traffic_sign_type,sign.traffic_sign_elements[0].traffic_sign_element_id) #testing the traffic sign type property

        #testing to see if the priority signs have been assigned to the appropriate priority lanelets

        #taking out each lanelet which id is in the "priority lanelet" list
        for pl in priority_lanelets:
            for ll in l2cr.lanelet_network.lanelets:
                if ll.lanelet_id == pl:

            #taking out signs from the previously selected lanelet so it could be checked if the sign has the same position as a sign in the "priority signs" list
                    for sign_id in ll.traffic_signs:
                        ts = next(x for x in l2cr.lanelet_network.traffic_signs if x.traffic_sign_id==sign_id)
                
                #checking if those signs are in the same position
                        prio_sign = next(x for x in priority_signs if x.position[0] == ts.position[0] and x.position[1] == ts.position[1])
                        self.assertTrue(prio_sign) 

        #same logic just with yield lanelets and yield signs
        for yl in yield_lanelets:
            for ll in l2cr.lanelet_network.lanelets:
                if ll.lanelet_id == yl:
                    for sign_id in ll.traffic_signs:
                        ts = next(x for x in l2cr.lanelet_network.traffic_signs if x.traffic_sign_id==sign_id)
                        yield_sign = next(x for x in yield_signs if x.position[0] == ts.position[0] and x.position[1] == ts.position[1])
                        self.assertTrue(yield_sign)

        self.assertTrue(yield_lanelets)
        self.assertTrue(priority_lanelets)

        capturedOutput = io.StringIO() # Create StringIO object so the printf of the function wont show
        sys.stdout = capturedOutput   
        #inserting an empty list in the function 
        yield_signs, priority_signs, yield_lanelets, priority_lanelets, stop_lines = l2cr._right_of_way_to_traffic_sign(right_of_way_relation,{})
        sys.stdout = sys.__stdout__
        #as the map is empty, function will never create new lanelets
        self.assertFalse(yield_lanelets)
        self.assertFalse(priority_lanelets)
        
        


    def test__fix_relation_unequal_ways(self):
        l2cr = Lanelet2CRConverter() #object refered to as "self" in the source code
        l2cr(osm)

        #creating nodes for the right way
        nr1 = Node(1,0,0)
        nr2 = Node(2,1,0)
        nr3 = Node(3,2,0)

        #creating nodes for the left way, which will have a node that is missing on position (1,1) 
        nl1 = Node(4,0,1)
        nl2 = Node(5,2,1)

        #creating ways
        right_way = Way(1,["1","2","3"])
        left_way = Way(2,["4","5"])

        #adding nodes and the ways to our osm so we could check the result of the function
        osm.add_node(nr1)
        osm.add_node(nr2)
        osm.add_node(nr3)
        osm.add_node(nl1)
        osm.add_node(nl2)
        #osm.add_node(nl3)
        osm.add_way(right_way)
        osm.add_way(left_way)

        l2cr._fix_relation_unequal_ways(left_way,right_way)
        
        #check if left_way has got one more node
        self.assertEqual(len(left_way.nodes),3)

        #check the position of the new node / it should be in (1,1) 
        self.assertEqual(float(l2cr.osm.nodes["1006"].lat),1.0)
        self.assertEqual(float(l2cr.osm.nodes["1006"].lon),1.0)

        #note: when the longer path had (1,2,3), and shorter (1,2) - the function did not create the third on 3.

        right_way = Way(3,["1","2"])
        left_way = Way(4,["4","5"])
        osm.add_way(right_way)
        osm.add_way(left_way)

        l2cr._fix_relation_unequal_ways(left_way,right_way)
        self.assertEqual(right_way.nodes,["1","2"])
        self.assertEqual(left_way.nodes,["4","5"])

        right_way = Way(5,["1","2"])
        left_way = Way(6,["3","4","5"])
        osm.add_way(right_way)
        osm.add_way(left_way)

        l2cr._fix_relation_unequal_ways(left_way,right_way)
        self.assertEqual(len(right_way.nodes),3)
        self.assertEqual(len(left_way.nodes),3)

        self.assertEqual(right_way.nodes,["1","1003","2"])
        self.assertEqual(left_way.nodes,["3","4","5"])

        #TODO: try out more possible scenarios that this function will work with in the future

    def test__find_lanelet_ids_of_suitable_nodes(self):
        l2cr = Lanelet2CRConverter() #object refered to as "self" in the source code
        l2cr(osm)

        #creating nodes
        nr1 = Node("1",0,0)
        nr2 = Node("2",1,0)
        nr3 = Node("3",2,0)
        
        #adding the nodes to the osm
        osm.add_node(nr1)
        osm.add_node(nr2)
        osm.add_node(nr3)
        
        #creating a node dict for our function
        nodes_dict={"1":[11],"2":[22],"3":[33]}

        #calling a function
        val1 = l2cr._find_lanelet_ids_of_suitable_nodes(nodes_dict,"1")
        self.assertListEqual(val1,[11,11]) #11 for the same node and 11 for the node in proximity

        val2 = l2cr._find_lanelet_ids_of_suitable_nodes(nodes_dict,"2")
        self.assertListEqual(val2,[22,22])
        
        #lets add a node that will be close by to 1
        nr4 = Node ("4",0,2e-10)
        osm.add_node(nr4)
        nodes_dict["4"]=[44]
        val = l2cr._find_lanelet_ids_of_suitable_nodes(nodes_dict,"1")
        self.assertListEqual(val,[11,11,44])
        try:
            l2cr._find_lanelet_ids_of_suitable_nodes(nodes_dict,"10") #it should throw an exception as there is no key 10 in the node dictionary
        except:
            self.assertRaises(AttributeError)

    def test_node_distance(self):
        l2cr = Lanelet2CRConverter() #object refered to as "self" in the source code
        l2cr(osm)

        #creating our nodes
        nr1 = Node("1",0,0)
        nr2 = Node("2",1,0)
        
        #adding the nodes to the osm
        osm.add_node(nr1)
        osm.add_node(nr2)

        #calling the function
        function_distance = l2cr.node_distance("1","2")

        #calculating the distance based on our proj. and L2 distance
        vec1 = np.array(l2cr.proj(float(nr1.lon), float(nr1.lat)))
        vec2 = np.array(l2cr.proj(float(nr2.lon), float(nr2.lat)))
        real_dist = np.linalg.norm(vec1 - vec2)
        self.assertEqual(function_distance,real_dist)

    def test__convert_way_to_vertices(self):
        l2cr = Lanelet2CRConverter() #object refered to as "self" in the source code
        l2cr(osm)
        
        #creating nodes
        nr1 = Node(1,0,0)
        nr2 = Node(2,0,1)
        nl1 = Node(3,1,0)
        nl2 = Node(4,1,1)
        
        #adding the nodes to the osm
        osm.add_node(nr1)
        osm.add_node(nr2)
        osm.add_node(nl1)
        osm.add_node(nl2)

        #creating a way
        way = Way(1,["1","2","3","4"])
        
        #calling a function
        vert = l2cr._convert_way_to_vertices(way)

        self.assertEqual(len(vert),len(way.nodes)) #make sure that there are same number of vertices as nodes

        #test the position of the vertices
        list = [nr1,nr2,nl1,nl2]
        ctr=0
        for v in vert:
            x,y = l2cr.proj(float(list[ctr].lon),float(list[ctr].lat)) #getting the x and y coordinates
            ctr+=1
            x-=l2cr.origin_utm[0] #transforming the coordinates to match the vertices geo location
            y-=l2cr.origin_utm[1]
            self.assertEqual(v[0],x)
            self.assertEqual(v[1],y)

    def test_check_for_predecessor(self):
        l2cr = Lanelet2CRConverter() #object refered to as "self" in the source code
        
        #creating custom nodes
        n1r1 = Node(1,0,0)
        n1r2 = Node(2,0,1)
        n1l1 = Node(3,1,0)
        n1l2 = Node(4,1,1)

        #adding those nose to the osm
        osm.add_node(n1r1)
        osm.add_node(n1r2)
        osm.add_node(n1l1)
        osm.add_node(n1l2)
        
        
        #creating 2 ways that will be used for a way relation
        wayr1= Way("11",["1","2"])
        osm.add_way(wayr1)
        wayl1 = Way("12",["3","4"])
        osm.add_way(wayl1)

        
        #creating a way relation
        wayrel = WayRelation("111","12","11")
        osm.add_way_relation(wayrel)

        #creating the nodes that have the same location as the ones already in our way_relation/lanelet
        n2r1 = Node("5",0,1)
        n2l1 = Node("6",1,1)
        osm.add_node(n2r1)
        osm.add_node(n2l1)

        l2cr(osm)

        #calling the function
        val = l2cr._check_for_predecessors(n2l1.id_,n2r1.id_)

        #as our created way_relation has the same last nodes as the ones that we sent to the function, val should be a list of one element (our wayrel id)
        self.assertEqual(val[0],wayrel.id_)

    def test_check_for_successor(self):
        l2cr = Lanelet2CRConverter() #object refered to as "self" in the source code
        l2cr(osm)

        #creating custom nodes
        n1r1 = Node(1,0,0)
        n1r2 = Node(2,0,1)
        n1l1 = Node(3,1,0)
        n1l2 = Node(4,1,1)

        #adding those nose to the osm
        osm.add_node(n1r1)
        osm.add_node(n1r2)
        osm.add_node(n1l1)
        osm.add_node(n1l2)

        #creating 2 ways that will be used for a way relation
        wayr1= Way("11",["1","2"])
        osm.add_way(wayr1)
        wayl1 = Way("12",["3","4"])
        osm.add_way(wayl1)

        
        #creating a way relation
        wayrel = WayRelation("111","12","11")
        osm.add_way_relation(wayrel)

        #creating the nodes that have the same location as the ones already in our way_relation/lanelet
        n2r1 = Node("5",0,0)
        n2l1 = Node("6",1,0)
        osm.add_node(n2r1)
        osm.add_node(n2l1)

        l2cr(osm)

        #calling the function
        val = l2cr._check_for_successors(n2l1.id_,n2r1.id_)

        #as our created way_relation has the same last nodes as the ones that we sent to the function, val should be a list of one element (our wayrel id)
        self.assertEqual(val[0],wayrel.id_)
        return
    
   

    def test_convert_way_to_vertices(self):
        l2cr = Lanelet2CRConverter() #object refered to as "self" in the source code
        
        #creating custom nodes
        n1r1 = Node(100,0,0)
        n1r2 = Node(200,0,1)
        n1l1 = Node(300,1,0)
        n1l2 = Node(400,1,1)

        #adding those nose to the osm
        osm.add_node(n1r1)
        osm.add_node(n1r2)
        osm.add_node(n1l1)
        osm.add_node(n1l2)

        #creating 2 ways that will be used for a way relation
        way= Way("1111",["100","200","300","400"])
        osm.add_way(way)
        l2cr(osm)

        lanelet = l2cr._convert_way_to_vertices(way)

        #test the position of the lanelet's vertices
        list = [n1r1,n1r2,n1l1,n1l2]
        ctr=0
        for v in lanelet:
            x,y = l2cr.proj(float(list[ctr].lon),float(list[ctr].lat)) #getting the x and y coordinates
            ctr+=1
            x-=l2cr.origin_utm[0] #transforming the coordinates to match the vertices geo location
            y-=l2cr.origin_utm[1]
            self.assertEqual(v[0],x)
            self.assertEqual(v[1],y)

    def test__two_vertices_coincide(self):
        v1 = np.array([[0, 0], [0, 1]])
        v2 = np.array([[0, 0], [0, 1]])
        self.assertTrue(_two_vertices_coincide(v1,v2))

        v1 = np.array([[5, 0], [5, 1]])
        v2 = np.array([[0, 0], [0,1]])
        self.assertFalse(_two_vertices_coincide(v1,v2))

    def test_find_adjacencies_of_coinciding_ways(self):
        return


if __name__ == '__main__':
    unittest.main()       