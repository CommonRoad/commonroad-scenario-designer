import unittest
import numpy as np
import os
import unittest
from crdesigner.map_conversion.lanelet2.cr2lanelet import CR2LaneletConverter, OSMLanelet, Node, Way, WayRelation
from crdesigner.configurations.get_configs import get_configs
from commonroad.scenario.lanelet import Lanelet
from commonroad.common.file_reader import CommonRoadFileReader
from pyproj import Proj

#creating a testing vertices and a testing scenario from a test file (xml)
right_vertices = np.array([[0, 0], [1, 0], [2, 0]])
left_vertices = np.array([[0, 1], [1, 1], [2, 1]])
center_vertices = np.array([[0, .5], [1, .5], [2, .5]])
lanelet = Lanelet(left_vertices, center_vertices, right_vertices, 100)

left_vertices2 = np.array([[0, 0], [1, 0], [2, 0]])
right_vertices2 = np.array([[0, -1], [1, -1], [2, -1]])
center_vertices2 = np.array([[0, -0.5], [1, -0.5], [2, -0.5]])
lanelet2 = Lanelet(left_vertices2, center_vertices2, right_vertices2, 105)
lanelet2._adj_left = 100


#loading a file for a scenario
commonroad_reader = CommonRoadFileReader(
            f"{os.path.dirname(os.path.realpath(__file__))}/../test_maps/lanelet2/merging_lanelets_utm.xml"
        )

#creating a scenario with the .open() function
scenario, _ = commonroad_reader.open()
        
class TestCR2LaneletConverter(unittest.TestCase):
    def test_init(self):
        #test the initialization values without opening the scenario
        cr1 = CR2LaneletConverter()
        self.assertEqual(cr1.id_count,-1)
        self.assertIsNone(cr1.first_nodes) 
        self.assertIsNone(cr1.last_nodes) 
        self.assertIsNone(cr1.left_ways) 
        self.assertIsNone(cr1.right_ways)
        self.assertIsNone(cr1.lanelet_network)
        self.assertIsNone(cr1.origin_utm)
        self.assertEqual(cr1.proj,Proj("+proj=utm +zone=32 +ellps=WGS84")) #default proj
    
    def test_init_with_scenario(self):
        #test the initialization with the custom proj scenario
        custom_proj_scen = "+proj=utm +zone=59 south"
        cr1 = CR2LaneletConverter(custom_proj_scen) #object refered to as "self" in the source code
        self.assertEqual(cr1.proj,Proj(custom_proj_scen))

    def test_id_count(self):
        # test assigning id
        cr1 = CR2LaneletConverter()
        self.assertEqual(cr1.id_count, -1)
        self.assertEqual(cr1.id_count, -2)
        self.assertEqual(cr1.id_count, -3)
        cr2 = CR2LaneletConverter()
        self.assertEqual(cr2.id_count, -1)
        self.assertEqual(cr2.id_count, -2)
        self.assertEqual(cr2.id_count, -3)
    
    def test_call(self):
        #checking if the lanelet networks are the same
        cr1 = CR2LaneletConverter()

        #check if the dicts are empty
        self.assertFalse(cr1.first_nodes)
        self.assertFalse(cr1.last_nodes)
        self.assertFalse(cr1.left_ways)
        self.assertFalse(cr1.right_ways)
        
        osm = cr1(scenario)
        self.assertEqual(scenario.lanelet_network,cr1.lanelet_network) #check the lanelet network of the scenario
        self.assertEqual(cr1.origin_utm, cr1.proj(scenario.location.gps_longitude, scenario.location.gps_latitude)) #check the origin_utm of the scenario

    def test_convert_lanelet(self):
        cr1 = CR2LaneletConverter()
        osm = cr1(scenario)

        #calculating the number of way relations before and after the function
        len_of_way_relations_before = len(cr1.osm.way_relations)
        cr1._convert_lanelet(lanelet)
        len_of_way_relations_after = len(cr1.osm.way_relations)
        
        #save the id variable as the count rises at every call
        idCount = cr1.id_count + 1 
        last_way_relation = list(cr1.osm.way_relations)[-1]
        
        self.assertEqual(len_of_way_relations_after,len_of_way_relations_before+1) #testing if the function has added a way relation to the osm
        self.assertEqual(cr1.osm.way_relations[last_way_relation].left_way, str(idCount+2)) #testing the right id of the left way
        self.assertEqual(cr1.osm.way_relations[last_way_relation].right_way, str(idCount+1)) #testing the right id of the right way
        self.assertEqual(cr1.osm.way_relations[last_way_relation].id_, str(idCount)) #testing the right id of the created way relation
        self.assertEqual(cr1.osm.way_relations[last_way_relation].tag_dict, {'type': 'lanelet'}) #testing the right entry in the dict

    def test_create_nodes(self):
        cr = CR2LaneletConverter()
        osm = cr(scenario)

        tup = cr._create_nodes(lanelet,None,None)
        left_nodes = list(cr.osm.nodes)[-6:-3] #getting the last created leftNodes
        right_nodes = list(cr.osm.nodes)[-3:] #getting the last created right nodes
        
        self.assertEqual(left_nodes,tup[0]) #tup[0] is the list of the created left nodes from our function "create_nodes"
        self.assertEqual(right_nodes,tup[1]) #tup[1] is the list of the created right nodes from our function "create_nodes"

    def test_get_first_and_last_nodes_from_way(self):
        cr1 = CR2LaneletConverter()
        osm = cr1(scenario)
        cr1._convert_lanelet(lanelet)
      
        #getting the created ways from our lanelet
        last_left_way = list(cr1.osm._ways)[-2]
        last_right_way = list(cr1.osm._ways)[-1]

        #getting the first and the last nodes in a tuple
        leftNodeTuple = cr1._get_first_and_last_nodes_from_way(last_left_way,True) 
        rightNodeTuple = cr1._get_first_and_last_nodes_from_way(last_right_way,True)

        self.assertEqual(cr1.osm._ways[last_left_way].nodes[0], leftNodeTuple[0]) #testing if the first node in the corresponding way is the same as the first node in the tuple
        self.assertEqual(cr1.osm._ways[last_left_way].nodes[-1], leftNodeTuple[1]) #testing if the first node in the corresponding way is the same as the last node in the tuple
        self.assertEqual(cr1.osm._ways[last_right_way].nodes[0], rightNodeTuple[0]) #testing if the first node in the corresponding way is the same as the first node in the tuple
        self.assertEqual(cr1.osm._ways[last_right_way].nodes[-1], rightNodeTuple[1]) #testing if the first node in the corresponding way is the same as the last node in the tuple

    def test_create_nodes_from_vertices(self):
        cr1 = CR2LaneletConverter()
        osm = cr1(scenario)
        left_nodes = cr1._create_nodes_from_vertices(left_vertices)
        right_nodes = cr1._create_nodes_from_vertices(right_vertices)
        self.assertEqual(len(right_nodes),3) #test the size of the right node array
        self.assertEqual(len(left_nodes),3) #test the size of the left node array

        #as I have some problems with the inverse of "proj" function, I have created testLonRight and testLatRight variables
        #with the coordinates of the first right node (0,0) and the last left node (2,1)
        testLonRight, testLatRight = cr1.proj(cr1.origin_utm[0]+0, cr1.origin_utm[1]+0, inverse=True)
        self.assertEqual(str(testLonRight),cr1.osm.nodes[right_nodes[0]].lon) #test the lon coordinates of the node
        self.assertEqual(str(testLatRight),cr1.osm.nodes[right_nodes[0]].lat) #test the lat coordinate of the node
        testLonLeft, testLatLeft = cr1.proj(cr1.origin_utm[0]+2, cr1.origin_utm[1]+1, inverse=True)
        self.assertEqual(str(testLonLeft),cr1.osm.nodes[left_nodes[2]].lon) #test the lon coordinate of the node
        self.assertEqual(str(testLatLeft),cr1.osm.nodes[left_nodes[2]].lat) #test the lat coordinate of the node
        
    def test_get_potential_left_way(self):
        cr1 = CR2LaneletConverter()
        osm = cr1(scenario)

        # As I can not seem to insert my custom lanelets directly into the scenario, a new testing lanelet is created and will be compared to a lanelet already in the scenario
        # As the both sides (left and right) are being tested, both vertices of the existing lanelet have been created, and will be assigned to the new lanelet depending on the testing needs
        test_right = cr1.lanelet_network.lanelets[11].right_vertices 
        test_left = cr1.lanelet_network.lanelets[11].left_vertices 

        #testing the same direction, left side, meaning that the right vertices is equal to the opposing left
        laneletTest = Lanelet(test_right,center_vertices,right_vertices,lanelet_id = 150) # right_vertices of the new Lanelet are the same as left_vertices of the lanelet (id 11) that is already in the scenario.
        laneletTest._adj_left = 12 #assigning our lanelet[11] as the adjacent left to our test lanelet.
        laneletTest.adj_left_same_direction = True #if the direction is the same, then the left way should be equal to the right one of some other lanelet
        self.assertEqual(cr1._get_potential_left_way(laneletTest),cr1.right_ways.get(laneletTest.adj_left))

        #testing the different direction, left side, meaning that the left vertices are equal, but reversed (hence the [::-1])
        laneletTest = Lanelet(test_left[::-1],center_vertices,right_vertices,lanelet_id = 150)
        laneletTest._adj_left = 12 #assigning our lanelet[11] as the adjacent left to our test lanelet.
        laneletTest.adj_left_same_direction = False 
        self.assertEqual(cr1._get_potential_left_way(laneletTest),cr1.left_ways.get(laneletTest.adj_left))

    def test_get_potential_right_way(self):
        cr1 = CR2LaneletConverter()
        osm = cr1(scenario)

        #same logic as in the previous testing, just for the right side, same direction
        test_right = cr1.lanelet_network.lanelets[11].right_vertices 
        test_left = cr1.lanelet_network.lanelets[11].left_vertices 
        laneletTest = Lanelet(left_vertices,center_vertices,test_left,lanelet_id = 150) # new Lanelet has the same right_vertices as left_vertices of the lanelet (id 11) that is already in the scenario.
        laneletTest._adj_right = 12 #assigning our lanelet[11] (it has id 12) as the adjacent left to our test lanelet.
        laneletTest.adj_right_same_direction = True 
        self.assertEqual(cr1._get_potential_right_way(laneletTest),cr1.left_ways.get(laneletTest.adj_right))

        #right side, different direction
        laneletTest = Lanelet(left_vertices,center_vertices,test_right[::-1],lanelet_id = 150) # new Lanelet has the same right_vertices as left_vertices of the lanelet (id 11) that is already in the scenario.
        laneletTest._adj_right = 12 #assigning our lanelet[11] (it has id 12) as the adjacent left to our test lanelet.
        laneletTest.adj_right_same_direction = False
        self.assertEqual(cr1._get_potential_right_way(laneletTest),cr1.right_ways.get(laneletTest.adj_right))
    
    def test_get_shared_first_nodes_from_other_lanelets(self):
        cr1 = CR2LaneletConverter()
        osm = cr1(scenario)
        #creating a lanelet that will have the same first nodes as some random lanelet already in the scenario
        lv = np.array([[-134.8145,22.3995],[-135,23]]) #same beginning of the node, end does not matter
        rv = np.array([[-134.791,25.5844],[-135,26]]) #same beginning of the node, end does not matter
        cv = np.array([[0,0],[0,0]]) #does not matter
        laneletTest = Lanelet(lv,rv,cv,100)
        laneletTest.predecessor = [2] #adding the lanelet which coordinates have been used in vertices as the predecessor

        #calling the function
        nodes = cr1._get_shared_first_nodes_from_other_lanelets(laneletTest)

        #if the function works accordingly, the value of the "nodes" variable should be equal to the value of the cr1.last_nodes at the same index of our lanelet 2. 
        self.assertEqual(nodes,cr1.last_nodes[2])
        cr1.lanelet_network.remove_lanelet(laneletTest)

    def test_get_shared_last_nodes_from_other_lanelets(self):
        cr1 = CR2LaneletConverter()
        osm = cr1(scenario)
        #creating a lanelet that will have the same first nodes as some random lanelet already in the scenario
        lv = np.array([[-79,15],[-80.9075,16.1302]]) #same beginning of the node, end does not matter
        rv = np.array([[-79,18],[-80.3486,19.5818]]) #same beginning of the node, end does not matter
        cv = np.array([[0,0],[0,0]]) #does not matter
        laneletTest = Lanelet(lv,rv,cv,100)
        laneletTest.successor = [2] #adding the lanelet which coordinates have been used in vertices as the predecessor
        
        #calling the function
        nodes = cr1._get_shared_last_nodes_from_other_lanelets(laneletTest)

        #if the function works accordingly, the value of the "nodes" variable should be equal to the value of the cr1.first_nodes at the same index of our lanelet 2. 
        self.assertEqual(nodes,cr1.first_nodes[2])

if __name__ == '__main__':
    unittest.main()