"""
This class contains functions for converting a CommonRoad map into a .net.xml SUMO map
"""
from collections import defaultdict
from copy import deepcopy
from typing import Dict, Tuple, List

import matplotlib
from commonroad.geometry.shape import Polygon

matplotlib.use('TkAgg')
import itertools
import os
import random
import subprocess
import warnings
from xml.etree import cElementTree as ET

from commonroad.scenario.traffic_sign import SupportedTrafficSignCountry
from commonroad.scenario.traffic_sign_interpreter import TrafficSigInterpreter
from xml.dom import minidom

import networkx as nx
import numpy as np
import sumolib
from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.visualization.draw_dispatch_cr import draw_object
from matplotlib import pyplot as plt

# modified sumolib.net.* files
from .sumolib_net.node import Node
from .sumolib_net.edge import Edge
from .sumolib_net.lane import Lane

from crmapconverter.sumo_map.config import CR2SumoNetConfig
from .util import compute_max_curvature_from_polyline

try:
    import pycrcc
    from commonroad_cc.collision_detection.pycrcc_collision_dispatch import create_collision_object
    use_pycrcc = True
except ModuleNotFoundError:
    warnings.warn('Commonroad Collision Checker not installed, use shapely instead (slower).')
    import shapely as shl
    use_pycrcc = False

class CR2SumoMapConverter:
    """Converts CommonRoad map to sumo map .net.xml"""
    def __init__(self, lanelet_network:LaneletNetwork, conf:CR2SumoNetConfig = CR2SumoNetConfig(),
                 country_id: SupportedTrafficSignCountry=SupportedTrafficSignCountry.ZAMUNDA):
        """

        :param scenario: CommonRoad scenario to be converted
        :param conf: configuration file for additional map conversion parameters
        """
        self.lanelet_network = None
        self.lanelet_network = lanelet_network
        self.conf:CR2SumoNetConfig = conf

        self.nodes: Dict[int, Node] = {}  # all the nodes of the map, key is the node ID
        self.edges: Dict[str, Edge] = {}  # all the edges of the map, key is the edge ID
        self.points_dict: Dict[int, np.ndarray] = {}  # dictionary for the shape of the edges
        self.connections = defaultdict(list)  # all the connections of the map
        self.connection_shapes: Dict[Tuple[str,str],np.ndarray] = {}
        self.lanes_dict: Dict[int, Tuple[int,...]] = {}  # key is the ID of the edges and value the ID of the lanelets that compose it
        self.lanes: Dict[str, Lane] = {}
        self.edge_lengths = {}
        self.explored_lanelets = []  # list of the already explored lanelets
        self.max_vehicle_width = max(self.conf.veh_params['width'].values())
        self.trafic_sign_interpreter:TrafficSigInterpreter = TrafficSigInterpreter(country_id, self.lanelet_network)
        self.lane_id2lanelet_id: Dict[str, int] = {}
        self.lanelet_id2lane_id: Dict[int, str] = {}
        self.lanelet_id2edge_id: Dict[int, int] = {}
        self.start_nodes = {}
        self.end_nodes = {}


    @classmethod
    def from_file(cls, file_path_cr, conf: CR2SumoNetConfig = CR2SumoNetConfig()):
        scenario, _ = CommonRoadFileReader(file_path_cr).open()
        return cls(scenario.lanelet_network, conf)

    def convert_net(self):
        # simplification steps
        # self._merge_junctions(self.conf.max_node_distance)
        self._find_lanes()
        self._init_nodes()
        self._create_sumo_edges_and_lanes()
        self._init_connections()
        # self._merge_junction_clustering(self.conf.max_node_distance)
        self._merge_junctions_intersecting_lanelets()
        self._filter_edges()
        # self._simplify_connections_new()
        self._create_lane_based_connections()
        # self._detect_zippers(self.merged_dictionary)
        # self._simplify_connections()
        #self.simplified_connections = self.connections

        # getting the parameters that will be returned
        # number_of_junctions = self._calculate_number_junctions()
        # speeds_list = self._get_speeds_list()

        # return self.points_dict, total_lanes_length, number_of_junctions, speeds_list

    def _find_lanes(self):
        """
        Convert a CommonRoad net into a SUMO net
        sumo_net contains the converted net
        points_dict contains the shape of the edges
        :return: sumo_net, points_dict
        """
        node_id = 0  # running node_id, will be increased for every new node
        self.points_dict = {lanelet.lanelet_id: lanelet.center_vertices for lanelet in self.lanelet_network.lanelets}

        plt.figure(figsize=[25,25])
        draw_object(self.lanelet_network, draw_params={'lanelet':{'show_label':True}})
        plt.draw()
        plt.autoscale()
        plt.ion()
        plt.axis('equal')
        plt.pause(0.001)

        for lanelet in self.lanelet_network.lanelets:
            edge_id = lanelet.lanelet_id
            successors = set(lanelet.successor)

            # prevent the creation of  multiple edges instead of edges with multiple lanes
            if edge_id in self.explored_lanelets:
                continue

            self.explored_lanelets.append(edge_id)
            adj_right_id = lanelet._adj_right
            adj_left_id = lanelet._adj_left
            right_same_direction = lanelet.adj_right_same_direction
            left_same_direction = lanelet.adj_left_same_direction
            lanelets = [lanelet]

            start_node_list = []
            end_node_list = []
            start_node_coordinates = lanelet.center_vertices[0]
            start_node_list.append(start_node_coordinates)
            end_node_coordinates = lanelet.center_vertices[-1]
            end_node_list.append(end_node_coordinates)
            # find rightmost lanelet
            rightmost_lanelet = lanelet
            zipper = False
            while adj_right_id is not None and right_same_direction is not False:
                self.explored_lanelets.append(adj_right_id)
                # Get start and end nodes of right adjacency.
                right_lanelet = self.lanelet_network.find_lanelet_by_id(adj_right_id)
                if right_lanelet.successor is not None:
                    if len(successors.intersection(set(right_lanelet.successor))) > 0:
                        zipper = True
                    successors = successors.union(set(right_lanelet.successor))
                adj_right_start = right_lanelet.center_vertices[0]
                start_node_list.append(adj_right_start)
                adj_right_end = right_lanelet.center_vertices[-1]
                end_node_list.append(adj_right_end)
                lanelets.append(right_lanelet)
                rightmost_lanelet = right_lanelet
                adj_right_id = right_lanelet._adj_right
                right_same_direction = right_lanelet.adj_right_same_direction



            # find leftmost lanelet
            while adj_left_id is not None and left_same_direction is not False:
                self.explored_lanelets.append(adj_left_id)
                # Get start and end nodes of left adjacency.
                left_lanelet = self.lanelet_network.find_lanelet_by_id(adj_left_id)
                if left_lanelet.successor is not None:
                    if len(successors.intersection(set(left_lanelet.successor))) > 0:
                        zipper = True
                    successors = successors.union(set(left_lanelet.successor))
                adj_left_start = left_lanelet.center_vertices[0]
                start_node_list.append(adj_left_start)
                adj_left_end = left_lanelet.center_vertices[-1]
                end_node_list.append(adj_left_end)
                lanelets.append(left_lanelet)
                adj_left_id = left_lanelet._adj_left
                left_same_direction = left_lanelet.adj_left_same_direction

            # order lanelets
            current_lanelet = rightmost_lanelet
            ordered_lanelet_ids = [current_lanelet.lanelet_id]
            while len(lanelets) != len(ordered_lanelet_ids):
                ordered_lanelet_ids.append(current_lanelet.adj_left)
                current_lanelet = self.lanelet_network.find_lanelet_by_id(ordered_lanelet_ids[-1])

            self.lanes_dict.update({rightmost_lanelet.lanelet_id: tuple(ordered_lanelet_ids)})
            self.edge_lengths[rightmost_lanelet.lanelet_id] = np.min([lanelet.distance[-1] for lanelet in lanelets])

            for i_lane, l_id in enumerate(ordered_lanelet_ids):
                self.lanelet_id2edge_id[l_id] = rightmost_lanelet.lanelet_id

    def _compute_node_coords(self, lanelets, index:int):
        vertices = np.array([l.center_vertices[index] for l in lanelets])
        return np.mean(vertices, axis=0)

    def _create_node(self, edge_id, lanelet_ids:Tuple[int], node_type:str):
        """
        Creates new node for an edge or assigns it to an existing node.
        :param edge_id: edge ID
        :param lanelets: list of lanelet ids
        :param node_type: 'from' or 'to'
        :return:
        """
        assert node_type == "from" or node_type == "to"
        if node_type == "from":
            index = 0
            if edge_id in self.start_nodes:
                # already assigned to a node, see @REFERENCE_1
                return
        else:
            index = -1
            if edge_id in self.end_nodes:
                return

        conn_edges = set()
        lanelets = []
        for l_id in lanelet_ids:
            lanelet_tmp = self.lanelet_network.find_lanelet_by_id(l_id)
            lanelets.append(lanelet_tmp)
            if lanelet_tmp is not None:
                if node_type == "to":
                    conn_lanelet = lanelet_tmp.successor
                else:
                    conn_lanelet = lanelet_tmp.predecessor

                if conn_lanelet is not None:
                    [conn_edges.add(self.lanelet_id2edge_id[succ]) for succ in conn_lanelet]

        if len(conn_edges) > 0:
            node_candidates = []
            if node_type == "from":
                node_list_other = self.end_nodes
            else:
                node_list_other = self.start_nodes

            # check if connected edges already have a start/end node
            for to_edg in conn_edges:
                if to_edg in node_list_other:
                    node_candidates.append(node_list_other[to_edg])

            # check: connected edges should already use the same node
            assert len(set(node_candidates)) <= 1, 'Unexpected error, please report!'
            if node_candidates:
                # assign existing node
                if node_type == "from":
                    self.start_nodes[edge_id] = node_candidates[0]
                else:
                    self.end_nodes[edge_id] = node_candidates[0]
            else:
                # create new node
                coords = self._compute_node_coords(lanelets, index=index)
                self.nodes[self.node_id_next] = Node(self.node_id_next, node_type, coords, [])
                # @REFERENCE_1
                if node_type == "from":
                    self.start_nodes[edge_id] = self.node_id_next
                    for conn_edg in conn_edges:
                        self.end_nodes[conn_edg] = self.node_id_next
                else:
                    self.end_nodes[edge_id] = self.node_id_next
                    for conn_edg in conn_edges:
                        self.start_nodes[conn_edg] = self.node_id_next

                self.node_id_next += 1
        else:
            # dead end
            coords = self._compute_node_coords(lanelets, index=index)
            self.nodes[self.node_id_next] = Node(self.node_id_next, node_type, coords, [])
            if node_type == "from":
                self.start_nodes[edge_id] = self.node_id_next
            else:
                self.end_nodes[edge_id] = self.node_id_next

            self.node_id_next += 1

    def _init_nodes(self):
        # creation of the start and end nodes
        # start node
        start_nodes = {}  # contains start nodes of each edge{edge_id: node_id}
        end_nodes = {}  # contains end nodes of each edge{edge_id: node_id}
        self.node_id_next = 1
        self.start_nodes = {}
        self.end_nodes = {}
        for edge_id, lanelet_ids in self.lanes_dict.items():
            self._create_node(edge_id, lanelet_ids, 'from')
            self._create_node(edge_id, lanelet_ids, 'to')

    def _create_sumo_edges_and_lanes(self):
        """
        Creates edges for net file with previously collected edges and nodes.
        :return: 
        """

        for edge_id, lanelet_ids in self.lanes_dict.items():
            # new_nodes[node_id] =
            # # create node
            #
            #
            # end_node = Node(node_id, node_type, end_node_coordinates, [])
            # self.nodes.update({str(node_id): end_node})
            # nodeB = end_node
            # node_id += 1
            #
            #
            # toAdd = True
            # for key, node_temp in self.nodes.items():
            #     temp_coord = np.array(node_temp.getCoord())
            #     # if tempx == node_x and tempy == node_y:
            #     for node in start_node_list:
            #         # if (temp_coord == node).all():
            #         if np.max(np.linalg.norm(temp_coord - node)) <= 0.5:
            #             toAdd = False
            #             nodeA = node_temp
            #             break
            #
            # if toAdd:
            #     node_type = 'right_before_left'
            #     start_node = Node(node_id, node_type, start_node_coordinates, [])
            #     self.nodes.update({str(node_id): start_node})
            #     nodeA = start_node
            #     node_id += 1
            #
            # # end node
            # toAdd = True
            # for key, node_temp in self.nodes.items():
            #     temp_coord = node_temp.getCoord()
            #     tempx = temp_coord[0]
            #     tempy = temp_coord[1]
            #     temp_coord = np.array([tempx,tempy])
            #     for node in end_node_list:
            #         if np.max(np.linalg.norm(temp_coord - node)) <= 0.5:
            #             toAdd = False
            #             nodeB = node_temp
            #             break
            #
            # if toAdd:


            # calculation of the length of a lane, lanes that belong to the same edge have the same length

            # Creation of Edge, using id as name
            start_node = self.nodes[self.start_nodes[edge_id]]
            end_node = self.nodes[self.end_nodes[edge_id]]
            # TODO: create priority from right of way rule in CR file
            edge = Edge(id=edge_id, fromN=start_node, toN=end_node,
                        prio=1, function='normal', name=edge_id)
            self.edges.update({str(edge_id): edge})
            if self.conf.overwrite_speed_limit is not None:
                speed_limit = self.conf.overwrite_speed_limit
            else:
                speed_limit = self.trafic_sign_interpreter.speed_limit(frozenset([lanelet.lanelet_id]))
                if speed_limit is None or np.isinf(speed_limit):
                    speed_limit = self.conf.unrestricted_speed_limit_default


            for lanelet_id in lanelet_ids:
                shape = self.points_dict.get(lanelet_id)
                lanelet = self.lanelet_network.find_lanelet_by_id(lanelet_id)
                lanelet_width = self._calculate_lanelet_width_from_cr(lanelet)
                max_curvature = compute_max_curvature_from_polyline(shape)
                # if lanelet_width <= self.max_vehicle_width:
                #     raise ValueError(
                #         "The lanelet width {} meters on lanelet {} is smaller than the allowed maximum vehicle width {} meters!".format(
                #             lanelet_width, lanelet_id, self.max_vehicle_width))
                disallow = self._filter_disallowed_vehicle_classes(max_curvature, lanelet_width, lanelet_id)

                lane = Lane(edge, speed_limit, self.edge_lengths[edge_id], width=lanelet_width,
                            allow=None, disallow=disallow, shape=shape)
                self.lanes[lane.getID()] = lane
                self.lane_id2lanelet_id.update({lane.getID(): lanelet_id})
                self.lanelet_id2lane_id.update({lanelet_id: lane.getID()})

        # set oncoming lanes
        for edge_id, lanelet_ids in self.lanes_dict.items():
            leftmost_lanelet = self.lanelet_network.find_lanelet_by_id(lanelet_ids[-1])
            if leftmost_lanelet.adj_left is not None:
                self.lanes[self.lanelet_id2lane_id[lanelet_ids[-1]]]\
                    .setAdjacentOpposite(self.lanelet_id2lane_id[leftmost_lanelet.adj_left])

    def _init_connections(self):
        """
        Init connections, doesn't consider junctions yet.
        :return:
        """
        for l in self.lanelet_network.lanelets:
            if l.successor is not None:
                self.connections[self.lanelet_id2lane_id[l.lanelet_id]].extend(
                [self.lanelet_id2lane_id[succ] for succ in l.successor])

    def _filter_disallowed_vehicle_classes(self, max_curvature:float, lanelet_width, lanelet_id) -> str:
        """
        Filter out the vehicle classes which should be disallowed on a specific lanelet due to large curvature.
        :param max_curvature: maximum curvature of the lanelet
        :param lanelet_width: width of the lanelet
        :param lanelet_id:
        :return: string of disallowed classes
        """
        if max_curvature > 0.001:  # not straight lanelet
            radius = 1 / max_curvature
            max_vehicle_length_sq = 4 * ((radius + lanelet_width / 2) ** 2 - (radius + self.max_vehicle_width / 2) ** 2)

            # select the disallowed vehicle classes
            disallow = None
            for veh_class, veh_length in self.conf.veh_params['length'].items():
                # only disallow vehicles longer than car (class passenger)
                if veh_length ** 2 > max_vehicle_length_sq and veh_length > self.conf.veh_params['length']['passenger']:
                    if disallow is not None:
                        disallow = veh_class + ' ' + disallow
                    else:
                        disallow = veh_class
                    # print("{} disallowed on lanelet {}, allowed max_vehicle_length={}".format(veh_class, lanelet_id,
                    #                                                                           max_vehicle_length))
        else:
            disallow = None

        return disallow

    @staticmethod
    def _calculate_lanelet_width_from_cr(lanelet):
        """
        Calculate the average width of a lanelet.
        :param lanelet: the lane whose width is to be calculated
        :return: average_width
        """
        helper_matrix = lanelet.right_vertices - lanelet.left_vertices
        distance_array = np.sqrt(helper_matrix[:,0] ** 2 + helper_matrix[:,1] ** 2)
        average_width = np.average(distance_array)
        return average_width

    # def _calculate_total_lanes_length(self):
    #     """
    #     Calculate the total lanes length of the map
    #     :return: total_lanes_length
    #     """
    #     total_lanes_length = 0
    #     for edge in self.edges.values():
    #         for lane in edge.getLanes():
    #             total_lanes_length += lane.getLength()
    #
    #     return total_lanes_length

    def _get_speeds_list(self):
        """
        Return a set of the speed limits of the edges
        :return: speeds_list
        """
        speeds_list = [] #list of speed that will be returned by the method
        for edge in self.new_edges.values():
            speed = edge.getSpeed()
            speeds_list.append(speed)
        speeds_list = set(speeds_list)
        return speeds_list

    def _calculate_number_junctions(self):
        """
        Calculate the number of junctions, nodes that don't represent a junction are not counted
        :return: number of junctions
        """
        number_of_junctions = 0
        for nodes in self.merged_dictionary.values():
            if len(nodes) != 1:
                number_of_junctions += 1
        return number_of_junctions

    #todo: not used anymore
    def _merge_junctions(self, max_node_distance):
        """
        Merging nodes into one junction based on the parameter max_node_distance
        :param max_node_distance: nodes that are closer than this value will be merged (value in meters)
        :return: nothing
        """
        warnings.warn('use _merge_junction_clustering instead', category=DeprecationWarning)
        self.new_nodes = {} #new dictionary for the merged nodes
        self.new_edges = {} #new dictionary for the edges after the simplifications
        self.merged_dictionary = {} #key is the merged node, value is a list of the nodes that form the merged node

        explored_nodes = []
        for node_id, current_node in self.nodes.items():
            merged_nodes = []
            if current_node not in explored_nodes:
                explored_nodes.append(current_node)
                merged_nodes.append(current_node)
                node_id = current_node.getID()
                # find merge candidates first
                for node in self.nodes.values():
                    incomings = current_node.getIncoming()
                    outgoings = current_node.getOutgoing()
                    num_connected = len(incomings) + len(outgoings)
                    if current_node == node or num_connected == 1:
                        continue
                    current_node_coordinates = np.asarray(current_node.getCoord())
                    node_coordinates = np.asarray(node.getCoord())
                    distance = np.linalg.norm(current_node_coordinates - node_coordinates)
                    if distance < max_node_distance:
                        merged_nodes.append(node)
                        if len(merged_nodes) == 1:
                            explored_nodes.append(node)

                # detailed graph search for nodes to merge
                if len(merged_nodes) > 1:
                    # Create graph for candidate nodes
                    Net = nx.Graph()
                    for node in merged_nodes:
                        Net.add_node(node.getID())
                    for edge_id, edge in self.edges.items():
                        fromNode = edge.getFromNode().getID()
                        toNode = edge.getToNode().getID()
                        if Net.has_node(fromNode) and Net.has_node(toNode):
                            Net.add_edge(fromNode, toNode, length=edge.getLength())

                    # Choose necessary nodes for merging using graph search
                    merged_nodes_in_graph = [current_node]
                    for node in merged_nodes:
                        u = current_node.getID()
                        v = node.getID()
                        if current_node != node and nx.algorithms.has_path(Net, u,v):
                            graph_distance = nx.algorithms.shortest_paths.dijkstra_path_length(Net, u, v, weight='length')
                            if graph_distance < max_node_distance:
                                merged_nodes_in_graph.append(node)
                                explored_nodes.append(node)  # toModify
                    merged_nodes = merged_nodes_in_graph

                x_coord, y_coord = self._calculate_avg_nodes(merged_nodes)
                coordinates = []
                coordinates.append(x_coord)
                coordinates.append(y_coord)
                merged_node = Node(node_id, 'priority', coordinates, []) #new merged node
                self.new_nodes.update({node_id: merged_node})
                self.merged_dictionary.update({current_node: merged_nodes})

    def _merge_junction_clustering(self, max_node_distance):
        """
        Merging nodes into one junction based on the parameter max_node_distance
        :param max_node_distance: nodes that are closer than this value will be merged (value in meters)
        :return: nothing
        """
        self.new_nodes = {} #new dictionary for the merged nodes
        self.new_edges = {} #new dictionary for the edges after the simplifications
        self.merged_dictionary = {} #key is the merged node, value is a list of the nodes that form the merged node

        explored_nodes = []
        for node_id, current_node in self.nodes.items():
            merged_nodes = [current_node]

            if current_node not in explored_nodes:
                queue = [current_node]
                i=0
                # expand all connected nodes until length of connecting edge > max_node_distance
                while len(queue) > 0:
                    assert i < 10000, 'Something went wrong'
                    i += 1
                    expanded_node = queue.pop()
                    incomings = expanded_node.getIncoming()
                    outgoings = expanded_node.getOutgoing()
                    for edge_in in incomings:
                        if edge_in.getLength() < max_node_distance:
                            to_node = edge_in.getFromNode()
                            if not to_node in explored_nodes:
                                merged_nodes.append(to_node)
                                queue.append(to_node)
                                explored_nodes.append(to_node)

                    for edge_out in outgoings:
                        if edge_out.getLength() < max_node_distance:
                            from_node = edge_out.getToNode()
                            if not from_node in explored_nodes:
                                merged_nodes.append(from_node)
                                queue.append(from_node)
                                explored_nodes.append(from_node)

                x_coord, y_coord = self._calculate_avg_nodes(merged_nodes)
                coordinates = []
                coordinates.append(x_coord)
                coordinates.append(y_coord)
                # self._detect_zipper()
                merged_node = Node(node_id, 'priority', coordinates, []) #new merged node
                self.new_nodes.update({node_id: merged_node})
                self.merged_dictionary.update({current_node: merged_nodes})

    def _merge_junctions_intersecting_lanelets(self):
        """
        Merge nodes when their connecting edges intersect.
        :return:
        """
        self.new_nodes = {}  # new dictionary for the merged nodes
        self.new_edges = {}  # new dictionary for the edges after the simplifications
        self.merged_dictionary = {}  # key is the merged node, value is a list of the nodes that form the merged node
        self.replaced_nodes = defaultdict(list)
        erode_lanelet_network = _erode_lanelets(self.lanelet_network, 0.3)

        polygons_dict = {}
        explored_nodes = []
        skip=0
        for node_id, current_node in self.nodes.items():
            merged_nodes = [current_node]
            junction_shapes = {}
            if current_node not in explored_nodes:
                queue = [current_node]
                i = 0
                # expand all connected nodes until length of connecting edge > max_node_distance
                while len(queue) > 0:
                    assert i < 10000, 'Something went wrong'
                    i += 1
                    expanded_node = queue.pop()
                    if expanded_node in explored_nodes: continue
                    incomings: List[Edge] = expanded_node.getIncoming()
                    outgoings: List[Edge] = expanded_node.getOutgoing()
                    edge_shapes_dict = {}
                    for edge_in in incomings:
                        edge_shape = []
                        for lanelet_id in (self.lanes_dict[edge_in.getID()][0], self.lanes_dict[edge_in.getID()][-1]):
                            if not lanelet_id in polygons_dict:
                                polygon = erode_lanelet_network.find_lanelet_by_id(lanelet_id).convert_to_polygon()
                                if use_pycrcc:
                                    polygons_dict[lanelet_id] = create_collision_object(polygon)
                                else:
                                    polygons_dict[lanelet_id] = polygon.shapely_object

                            edge_shape.append(polygons_dict[lanelet_id])

                        edge_shapes_dict[edge_in.getID()] = edge_shape

                    for edge_id, edge_shape in edge_shapes_dict.items():
                        for edge_id_other, junction_shape_other in junction_shapes.items():
                            if edge_id == edge_id_other: continue
                            edges_intersect = False
                            for shape in edge_shape:
                                if edges_intersect:
                                    break
                                for shape_other in junction_shape_other:
                                    if use_pycrcc:
                                        # pycrcc
                                        if shape.collide(shape_other):
                                            from_node = self.edges[str(edge_id)].getFromNode()
                                            merged_nodes.append(from_node)
                                            explored_nodes.append(from_node)
                                            queue.append(from_node)
                                            edges_intersect = True
                                            break
                                    else:
                                        # shapely
                                        if shape.intersection(shape_other).area > 0.0:
                                            from_node = self.edges[str(edge_id)].getFromNode()
                                            merged_nodes.append(from_node)
                                            explored_nodes.append(from_node)
                                            queue.append(from_node)
                                            edges_intersect = True
                                            break

                        for edge_id_other, edge_shape_other in edge_shapes_dict.items():
                            if edge_id == edge_id_other: continue
                            edges_intersect = False
                            for shape in edge_shape:
                                if edges_intersect:
                                    break
                                for shape_other in edge_shape_other:
                                    if use_pycrcc:
                                        # pycrcc
                                        if shape.collide(shape_other):
                                            junction_shapes.update({edge_id: edge_shape})
                                            junction_shapes.update({edge_id_other: edge_shape_other})
                                            from_nodes = [self.edges[str(edge_id)].getFromNode(),
                                                          self.edges[str(edge_id_other)].getFromNode()]
                                            merged_nodes.extend(from_nodes)
                                            explored_nodes.extend(from_nodes)
                                            queue.extend(from_nodes)
                                            edges_intersect = True
                                            break
                                    else:
                                        # shapely
                                        if shape.intersection(shape_other).area > 0.0:
                                            junction_shapes.update({edge_id: edge_shape})
                                            junction_shapes.update({edge_id_other: edge_shape_other})
                                            from_nodes = [self.edges[str(edge_id)].getFromNode(),
                                                          self.edges[str(edge_id_other)].getFromNode()]
                                            merged_nodes.extend(from_nodes)
                                            explored_nodes.extend(from_nodes)
                                            queue.extend(from_nodes)
                                            edges_intersect = True
                                            break

                    edge_shapes_dict = {}
                    for edge_out in outgoings:
                        edge_shape = []
                        for lanelet_id in (self.lanes_dict[edge_out.getID()][0], self.lanes_dict[edge_out.getID()][-1]):
                            if not lanelet_id in polygons_dict:
                                polygon = erode_lanelet_network.find_lanelet_by_id(lanelet_id).convert_to_polygon()
                                if use_pycrcc:
                                    polygons_dict[lanelet_id] = create_collision_object(polygon)
                                else:
                                    polygons_dict[lanelet_id] = polygon.shapely_object

                            edge_shape.append(polygons_dict[lanelet_id])

                        edge_shapes_dict[edge_out.getID()] = edge_shape

                    for edge_id, edge_shape in edge_shapes_dict.items():
                        for edge_id_other, junction_shape_other in junction_shapes.items():
                            if edge_id == edge_id_other: continue
                            edges_intersect = False
                            for shape in edge_shape:
                                if edges_intersect:
                                    break
                                for shape_other in junction_shape_other:
                                    if use_pycrcc:
                                        # pycrcc
                                        if shape.collide(shape_other):
                                            to_node = self.edges[str(edge_id)].getToNode()
                                            merged_nodes.append(to_node)
                                            explored_nodes.append(to_node)
                                            queue.append(to_node)
                                            edges_intersect = True
                                            break
                                            plt.figure()
                                            from commonroad_cc.visualization.draw_dispatch import draw_object as dr2
                                            dr2(shape)
                                            dr2(shape_other)
                                            plt.draw()
                                            plt.autoscale()
                                            plt.axis('equal')
                                            plt.pause(0.001)
                                            print('sdf')
                                    else:
                                        # shapely
                                        if shape.intersection(shape_other).area > 0.0:
                                            to_node = self.edges[str(edge_id)].getToNode()
                                            merged_nodes.append(to_node)
                                            explored_nodes.append(to_node)
                                            queue.append(to_node)
                                            edges_intersect = True
                                            break

                        for edge_id_other, edge_shape_other in edge_shapes_dict.items():
                            if edge_id == edge_id_other: continue
                            edges_intersect = False
                            for shape in edge_shape:
                                if edges_intersect:
                                    break
                                for shape_other in edge_shape_other:
                                    if use_pycrcc:
                                        # pycrcc
                                        if shape.collide(shape_other):
                                            junction_shapes.update({edge_id: edge_shape})
                                            junction_shapes.update({edge_id_other: edge_shape_other})
                                            to_nodes = [self.edges[str(edge_id)].getToNode(),
                                                        self.edges[str(edge_id_other)].getToNode()]
                                            merged_nodes.extend(to_nodes)
                                            explored_nodes.extend(to_nodes)
                                            queue.extend(to_nodes)
                                            edges_intersect = True
                                            break
                                    else:
                                        # shapely
                                        if shape.intersection(shape_other).area > 0.0:
                                            junction_shapes.update({edge_id: edge_shape})
                                            junction_shapes.update({edge_id_other: edge_shape_other})
                                            to_nodes = [self.edges[str(edge_id)].getToNode(),
                                                        self.edges[str(edge_id_other)].getToNode()]
                                            merged_nodes.extend(to_nodes)
                                            explored_nodes.extend(to_nodes)
                                            queue.extend(to_nodes)
                                            edges_intersect = True
                                            break

                x_coord, y_coord = self._calculate_avg_nodes(merged_nodes)
                coordinates = []
                coordinates.append(x_coord)
                coordinates.append(y_coord)
                # self._detect_zipper()
                merged_node = Node(self.node_id_next, 'priority', coordinates, [])  # new merged node
                self.node_id_next += 1
                self.new_nodes.update({merged_node.getID(): merged_node})
                merged_nodes = set([n.getID() for n in merged_nodes])

                for old_node in merged_nodes:
                    # assert not old_node in self.replaced_nodes
                    self.replaced_nodes[old_node].append(merged_node.getID())

                self.merged_dictionary.update({merged_node.getID(): merged_nodes})

        replace_nodes_old = deepcopy(self.replaced_nodes)
        explored_nodes_all = set()
        for old_node, new_nodes in replace_nodes_old.items():
            if old_node in explored_nodes_all:
                continue
            if len(new_nodes) > 1:
                new_candidates = deepcopy(new_nodes)
                new_node = new_nodes[0]
                merged_nodes = set()
                explored_candidates = set()
                while new_candidates:
                    # merge with merged junction
                    new_node_tmp = new_candidates.pop()
                    if new_node_tmp in explored_candidates: continue
                    explored_candidates.add(new_node_tmp)
                    merged_nodes = merged_nodes.union(self.merged_dictionary[new_node_tmp])
                    for merged_node in self.merged_dictionary[new_node_tmp]:
                        if len(self.replaced_nodes[merged_node]) > 1:
                            new_candidates = list(set(new_candidates + self.replaced_nodes[merged_node]).difference(explored_candidates))

                for node_id in explored_candidates:
                    del self.merged_dictionary[node_id]
                    if not node_id == new_node:
                        del self.new_nodes[node_id]
                self.merged_dictionary[new_node] = merged_nodes
                explored_nodes_all = explored_nodes_all.union(merged_nodes)
                for merged_node in merged_nodes:
                    self.replaced_nodes[merged_node] = [new_node]

        print('tock ')

    # self._detect_zipper

    def _filter_edges(self):
        """
        Remove edges that lie inside a junction. Those will be replaced by internal edges
        :return: nothing
        """
        for edge in self.edges.values():
            # remove_edge = self._consider_edge(edge)
            remove_edge = self._consider_edge_new(edge)
            if remove_edge:
                continue
            edge_id = edge.getID()
            start_id = edge.getFromNode().getID()
            end_id = edge.getToNode().getID()

            for new_node_id, merged_nodes in self.merged_dictionary.items():
                if start_id in merged_nodes:
                    edge.setFrom(self.new_nodes[new_node_id])
                    break

            for new_node_id, merged_nodes in self.merged_dictionary.items():
                if end_id in merged_nodes:
                    edge.setTo(self.new_nodes[new_node_id])
                    break

            self.new_edges.update({edge_id: edge})

    def _consider_edge(self, edge):
        """
        returns True if the edge must be removed, False otherwise
        :param edge: the edge to consider
        :return: flag remove_edge
        """
        remove_edge = False
        startNode = edge.getFromNode()
        endNode = edge.getToNode()
        startNodeID = startNode.getID()
        endNodeID = endNode.getID()

        for key, value in self.merged_dictionary.items():
            listIDs = []
            for node in value:
                listIDs.append(node.getID())
            if startNodeID in listIDs and endNodeID in listIDs:
                remove_edge = True

        return remove_edge

    def _consider_edge_new(self, edge):
        """
        returns True if the edge must be removed, False otherwise
        :param edge: the edge to consider
        :return: flag remove_edge
        """
        remove_edge = False
        startNode = edge.getFromNode()
        endNode = edge.getToNode()
        startNodeID = startNode.getID()
        endNodeID = endNode.getID()

        for new_node_id, merged_nodes in self.merged_dictionary.items():
            if startNodeID in merged_nodes and endNodeID in merged_nodes:
                remove_edge = True

        return remove_edge
    # def _simplify_connections(self):
    #     """
    #     Instantiate a new dictionary with only the connections that are meaningful after the simplification of the net
    #     :return: nothing
    #     """
    #     self.simplified_connections = {}
    #     for keyEdge, connections in self.connections.items():
    #         to_edges = []
    #         for connection in connections:
    #             next = self.connections[connection]
    #             to_edges = to_edges + next
    #         fromEdgeNew, toEdgesNew = self._redefine_connection(keyEdge, to_edges)
    #         mustAdd = self._check_addition(toEdgesNew)
    #         alreadyUpdated = False
    #         if len(to_edges) != 0 and mustAdd and fromEdgeNew in self.new_edges.keys():
    #             if fromEdgeNew in self.simplified_connections.keys():
    #                 toUpdate = self.simplified_connections.get(fromEdgeNew)
    #                 toUpdate = toUpdate + toEdgesNew
    #                 self.simplified_connections.update({fromEdgeNew: toUpdate})
    #                 alreadyUpdated = True
    #             if alreadyUpdated is False:
    #                 self.simplified_connections.update({fromEdgeNew: toEdgesNew})

    def _check_addition(self, to_edges):
        """
        Check if the connection is really to add
        :param to_edges: destination edges to check
        :return: True if the connection must be added, False otherwise
        """
        mustAdd = True
        for connection in to_edges:
            if connection not in self.new_edges.keys():
                mustAdd = False
        return mustAdd

    def _redefine_connection(self, from_edge, to_edges):
        """
        Substitute the ID of edges that were transformed into lanes with their corresponding edge ID
        :param from_edge: source Edge ID
        :param to_edges: destinations edges IDs
        :return: fromEdgeNew, toEdgesNew
        """
        toEdgesNew = []
        for master_edge, lanes in self.lanes_dict.items():
            if from_edge in lanes:
                fromEdgeNew = master_edge
            for edge in to_edges:
                if edge in lanes:
                    toEdgesNew.append(master_edge)
        return fromEdgeNew, toEdgesNew

    def _create_lane_based_connections(self):
        """
        Instantiate a new dictionary with only the connections that are meaningful after the simplification of the net
        :return: nothing
        """
        edge_ids = [str(edge.getID()) for edge in list(self.new_edges.values())]
        # print(self.connections)
        for from_lane, connections in self.connections.items():
            if from_lane.split("_")[0] not in edge_ids:
                continue
            explored_lanes = set()
            queue = [[via] for via in connections]  # list with edge ids to toLane
            paths = []
            # TODO verify same node!!
            # queue = set(copy.deepcopy(connections))
            # expand successor until non-internal (i.e. not in merged_nodes_all) edge is found
            while queue:
                # print(queue)
                current_path = queue.pop()
                succ_lane = current_path[-1]
                explored_lanes.add(succ_lane)
                if succ_lane.split("_")[0] not in edge_ids:
                    for next_lane in self.connections[succ_lane]:
                        if next_lane not in explored_lanes:
                            queue.append(current_path + [next_lane])
                else:
                    paths.append(current_path)

            # judge whether detailed lane id should be defined
            # to_lanes = [path[-1] for path in paths]
            for path in paths:
                if len(path) > 1:
                    shape = np.vstack([self.points_dict[self.lane_id2lanelet_id[lane_id]] for lane_id in path[:-1]])
                    via = path[1]
                else:
                    shape = None
                    via = None
                self.connection_shapes.update({(from_lane, via, path[-1]): shape})
        return
            # from_edge_new, to_edges_new = self._redifine_connection_new(from_lane, to_lanes) #25_1, [24_0]


            # mustAdd = self._check_addition_new([pair[1] for pair in via_successors])
            # alreadyUpdated = False
            # if len(to_edges_new) != 0 and int(from_edge_new.split("_")[0]) in self.new_edges.keys():
            #     if from_edge_new.split("_")[0] in self.simplified_connections.keys():
            #         toUpdate = self.simplified_connections.get(from_edge_new)
            #         toUpdate = toUpdate + to_edges_new
            #         self.simplified_connections.update({from_edge_new: toUpdate})
            #         for edge, shape in zip(to_edges_new, shapes):
            #             self.connection_shapes.update({(from_edge_new, edge): shape})
            #         alreadyUpdated = True
            #     if alreadyUpdated is False:
            #         self.simplified_connections.update({from_edge_new: to_edges_new})
            #         for edge, shape in zip(to_edges_new, shapes):
            #             self.connection_shapes.update({(from_edge_new,edge): shape})

    def _check_addition_new(self, toEdges):
        """
        Check if the connection is really to add
        :param toEdges: destination edges to check
        :return: True if the connection must be added, False otherwise
        """
        mustAdd = True
        for connection in toEdges:
            if int(connection.split("_")[0]) not in list(self.new_edges):
                mustAdd = False
        return mustAdd

    def _redifine_connection_new(self, fromEdge, toEdges, vias=None):
        """
        Substitute the ID of edges that were transformed into lanes with their corresponding edge ID and lane index
        :param fromEdge: source Edge ID
        :param toEdges: destinations edges IDs
        :return: fromEdgeNew, toEdgesNew
        """
        newEdges = []
        self.mapping = self._map_edgeID_to_laneIndex()
        fromEdgeNew = self.mapping.get(fromEdge)
        for edge_id in toEdges:
            new_pair = [None,None]
            newEdges.append(self.mapping.get(edge_id))

        return fromEdgeNew, newEdges

    def _map_edgeID_to_laneIndex(self):
        """
        Specify each lane with its edge_id and lane_index with the form {laneID: edgeID_ laneIndex}}
        :return:
        """
        self.mapping = {}
        for keyLane, lanes in self.lanes_dict.items():
            if len(lanes) == 1 and keyLane == lanes[0]:
                self.mapping.update({lanes[0]: str(keyLane) + '_0'}) #{keyLane: 0}})
            elif len(lanes) == 1 and keyLane != lanes[0]:
                raise ValueError('Wrongly named edge?')
            else:
                for laneIndex, lane in enumerate(lanes):
                    if lane not in self.mapping.keys():
                        self.mapping.update({lane: str(keyLane) + '_' + str(laneIndex)}) #TODO: Problem might exist w.r.t. index value. Better getIndex.

        return self.mapping

    def _calculate_avg_nodes(self, nodes):
        """
        Calculate the average of a given list of nodes
        :param nodes: list containing nodes
        :return: the coordinates of the average node, x and y
        """
        list_x = []
        list_y = []
        for node in nodes:
            coordinates = node.getCoord()
            list_x.append(coordinates[0])
            list_y.append(coordinates[1])
        average_x = np.sum(list_x) / len(list_x)
        average_y = np.sum(list_y) / len(list_y)
        return average_x, average_y

    def _getShapeString(self, shape):
        """
        Convert a collection of points from format shape  to string
        :param shape: a collection of point defining and edge
        :return: the same shape but in string format
        """
        shapeString = ""
        for point in shape:
            pointx = point[0]
            pointy = point[1]
            pointString = str(pointx) + "," + str(pointy)
            shapeString += pointString + " "
        return shapeString

    # def write_net(self, output_path):
    #     """
    #     Function for writing the edges and nodes files in xml format
    #     :param output_path: the relative path of the output
    #     :return: nothing
    #     """
    #     self._writeEdgesFile(output_path)
    #     self._write_nodes_file(output_path)
    #     self._write_connections_file(output_path)

    def write_net_new(self, output_path):
        """
        Function for writing the edges and nodes files in xml format
        :param output_path: the relative path of the output
        :return: None
        """
        self._write_edges_file(output_path)
        self._write_nodes_file(output_path)
        self._write_connections_file_new(output_path)

    def _write_edges_file(self, output_path):
        """
        Function for writing the edges file
        :param output_path: path for the file
        :return: nothing
        """
        with open(os.path.join(os.path.dirname(output_path), '_edges.net.xml'), 'w+') as output_file:
            sumolib.writeXMLHeader(output_file, '')
            root = ET.Element('root')
            edges = ET.SubElement(root, 'edges')
            for edge in self.new_edges.values():
                edge.getLanes()
                fromNode = str(edge.getFromNode().getID())
                edgeID = str(edge.getID())
                toNode = str(edge.getToNode().getID())
                numLanes = str(edge.getLaneNumber())
                function = str(edge.getFunction())
                edge_et = ET.SubElement(edges, 'edge')
                edge_et.set('from', fromNode)
                edge_et.set('id', edgeID)
                edge_et.set('to', toNode)
                edge_et.set('numLanes', numLanes)
                edge_et.set('spreadType', "center")
                edge_et.set('function', function)
                for lane in edge.getLanes():
                    laneID = str(lane.getIndex())
                    speed = str(lane.getSpeed())
                    length = str(lane.getLength())
                    width = str(lane.getWidth())
                    shape = lane.getShape()
                    shapeString = self._getShapeString(shape)
                    disallow = Lane.getDisallowed(lane)
                    lane = ET.SubElement(edge_et, 'lane')
                    lane.set('index', laneID)
                    lane.set('speed', speed)
                    lane.set('length', length)
                    lane.set('shape', shapeString)
                    lane.set('width', width)
                    if disallow is not None:
                        lane.set('disallow', disallow)
            output_str = ET.tostring(edges)
            reparsed = minidom.parseString(output_str)
            output_file.write(reparsed.toprettyxml(indent="\t"))

    def _write_nodes_file(self, output_path):
        """
        Functio for writing the nodes file
        :param output_path: path for the file
        :return: nothing
        """
        with open(os.path.join(os.path.dirname(output_path), '_nodes.net.xml'), 'w+') as output_file:
            sumolib.writeXMLHeader(output_file, '')
            root = ET.Element('root')
            nodes = ET.SubElement(root, 'nodes')
            for node in self.new_nodes.values():
                ET.SubElement(nodes, 'node', id=str(node.getID()), x=str(node.getCoord()[0]),
                              y=str(node.getCoord()[1]), function=node.getType())
            output_str = ET.tostring(nodes, encoding='utf8', method='xml').decode("utf-8")
            reparsed = minidom.parseString(output_str)
            output_file.write(reparsed.toprettyxml(indent="\t"))

    def _write_connections_file(self, output_path):
        """
        Function for writing the connections file
        :param output_path: path for the file
        :return: nothing
        """
        warnings.warn("deprecated", DeprecationWarning)
        with open(os.path.join(os.path.dirname(output_path), '_connections.net.xml'), 'w+') as output_file:
            sumolib.writeXMLHeader(output_file, '')
            root = ET.Element('root')
            connections = ET.SubElement(root, 'connections')
            for key, via_successors in self.simplified_connections.items():
                for pair in via_successors:
                    connection = ET.SubElement(connections, 'connection')
                    connection.set('from', str(key))
                    connection.set('to', str(pair[1]))
                    if pair[0] is not None:
                        connection.set('via', str(pair[0]))
            output_str = ET.tostring(connections, encoding='utf8', method='xml').decode("utf-8")
            reparsed = minidom.parseString(output_str)
            output_file.write(reparsed.toprettyxml(indent="\t"))

    def _write_connections_file_new(self, output_path):
        """
        Function for writing the connections file
        :param output_path: path for the file
        :return: nothing
        """
        with open(os.path.join(os.path.dirname(output_path), '_connections.net.xml'), 'w+') as output_file:
            sumolib.writeXMLHeader(output_file, '')
            root = ET.Element('root')
            connections = ET.SubElement(root, 'connections')
            for path, shape in self.connection_shapes.items():
                connection = ET.SubElement(connections, 'connection')
                connection.set('from', str(path[0].split('_')[0]))
                connection.set('to', str(path[2].split('_')[0]))
                connection.set('fromLane', str(path[0].split('_')[1]))
                connection.set('toLane', str(path[2].split('_')[1]))
                connection.set('contPos', str(self.conf.wait_pos_internal_junctions))
                if shape is not None:
                    connection.set('shape', self._getShapeString(shape))
                # if path[1] is not None:
                #     connection.set('via', str(path[1]))
            output_str = ET.tostring(connections, encoding='utf8', method='xml').decode("utf-8")
            reparsed = minidom.parseString(output_str)
            output_file.write(reparsed.toprettyxml(indent="\t"))

    @staticmethod
    def merge_files(output_path:str, cleanup=True) -> bool:
        """
        Function that merges the edges and nodes files into one using netconvert
        :param output_path: the relative path of the output
        :param cleanup: deletes temporary input files after creating net file (only deactivate for debugging)
        :return: bool: returns False if conversion fails
        """
        # The header of the xml files must be removed
        to_remove = ["options", "xml"]

        # Removing header in edges file
        with open(os.path.join(os.path.dirname(output_path), '_edges.net.xml'), 'r') as file:
            lines = file.readlines()
        with open(os.path.join(os.path.dirname(output_path), '_edges.net.xml'), 'w') as file:
            for line in lines:
                if not any(word in line for word in to_remove):
                    file.write(line)

        # Removing header in nodes file
        with open(os.path.join(os.path.dirname(output_path), '_nodes.net.xml'), 'r') as file:
            lines = file.readlines()
        with open(os.path.join(os.path.dirname(output_path), '_nodes.net.xml'), 'w') as file:
            for line in lines:
                if not any(word in line for word in to_remove):
                    file.write(line)

        # Removing header in connections file
        with open(os.path.join(os.path.dirname(output_path), '_connections.net.xml'), 'r') as file:
            lines = file.readlines()
        with open(os.path.join(os.path.dirname(output_path), '_connections.net.xml'), 'w') as file:
            for line in lines:
                if not any(word in line for word in to_remove):
                    file.write(line)

        nodesFile = os.path.join(os.path.dirname(output_path), '_nodes.net.xml')
        edgesFile = os.path.join(os.path.dirname(output_path), '_edges.net.xml')
        connectionsFile = os.path.join(os.path.dirname(output_path), '_connections.net.xml')
        output = output_path

        # Calling of Netconvert
        bashCommand = "netconvert --plain.extend-edge-shape=false " \
                      "--no-turnarounds=true " \
                      "--junctions.internal-link-detail=20 "\
                      "--geometry.avoid-overlap=true "\
                      "--offset.disable-normalization=true " \
                      "--node-files=" + str(nodesFile) + \
                      " --edge-files=" + str(edgesFile) + \
                      " --connection-files=" + str(connectionsFile) + \
                      " --output-file=" + str(output) + \
                      " --geometry.remove.keep-edges.explicit=true"
        # "--junctions.limit-turn-speed=6.5 " \
        # "--geometry.max-segment-length=15 " \
        success = True
        try:
            _ = subprocess.check_output(bashCommand.split(), timeout=5.0)
        except FileNotFoundError as e:
            if 'netconvert' in e.filename:
                warnings.warn("Is netconvert installed and added to PATH?")
            else:
                success = False
        except BaseException:
            success = False

        if cleanup is True and success:
            os.remove(nodesFile)
            os.remove(edgesFile)
            os.remove(connectionsFile)

        return success

    @staticmethod
    def rewrite_netfile(output:str):
        """
        Change the type of the junction node to zipper.
        :param output: the netfile to be modified.
        :return: None
        """
        tree = ET.parse(output)
        root = tree.getroot()
        junctions = root.findall("junction")
        for junction in junctions:
            for key, value in junction.attrib.items():
                if key == 'type' and (value == 'priority' or value == 'unregulated'):
                    junction.set(key, 'zipper')

        tree.write(output, encoding='utf-8', xml_declaration=True)

    def debug_lanelet_net(self, with_lane_id=True, with_succ_pred=False, with_adj=False, with_speed=False,
                          figure_title=None):
        """
        Debnug function for showing the CommonRoad map that has to be converted
        :param with_lane_id: specifies if printing the lane id or not
        :param with_succ_pred: specifies if showing the predecessors or not
        :param with_adj: specifies if showing the adjacents edges or not
        :param with_speed: specifies if showing the speed limit or not
        :param figure_title: specifies the title of the figure
        :return: nothing
        """
        plt.figure(figsize=(25, 25))
        if figure_title is not None:
            plt.title(figure_title)
        plt.gca().set_aspect('equal')
        draw_object(self.lanelet_network)

        # add annotations
        for l in self.lanelet_network.lanelets:
            # assure that text for two different lanelets starting on same position is placed differently
            noise = random.random()
            info = ''
            if with_lane_id:
                id = 'id: ' + str(l.lanelet_id)
                centroid = np.array(l.convert_to_polygon().shapely_object.centroid)
                plt.text(centroid[0], centroid[1], id, zorder=100, size=8,
                         color='r', verticalalignment='top')
            if with_succ_pred:
                info = info + '\nsucc: ' + str(l.successor) + ' pred: ' + str(l.predecessor)
            if with_adj:
                info = info + ' \nadj_l: ' + str(l.adj_left) + '; adj_l_same_dir: ' + str(l.adj_left_same_direction)
                info = info + ' \nadj_r: ' + str(l.adj_right) + '; adj_r_same_dir: ' + str(l.adj_right_same_direction)
            if with_speed:
                info = info + '\nspeed limit: ' + str(l.speed_limit)
            plt.plot(l.center_vertices[0, 0], l.center_vertices[0, 1], 'x')
            plt.text(l.center_vertices[0, 0] + noise, l.center_vertices[0, 1] + noise, info, zorder=100, size=8,
                     verticalalignment='top')
        plt.show()

    def convert_to_net_file(self, output_file:str):
        """Convert the Commonroad scenario to a net.xml file, specified by the absolute  path output_file."""
        self.convert_net()
        self.write_net_new(output_file)
        self.merge_files(output_file)


def _erode_lanelets(lanelet_network: LaneletNetwork, radius: float) -> LaneletNetwork:
    """Erode shape of lanelet by given radius."""

    lanelets_ero = []
    crop_meters = 0.3
    min_factor = 0.1
    for lanelet in lanelet_network.lanelets:
        lanelet_ero = deepcopy(lanelet)

        # shorten lanelet by radius
        if len(lanelet_ero._center_vertices) > 3:
            i_max = int(np.floor(len(lanelet_ero._center_vertices) - 1 / 2))

            i_crop_0 = np.argmax(lanelet_ero.distance >= crop_meters)
            i_crop_1 = len(lanelet_ero.distance) - np.argmax(
                lanelet_ero.distance >= lanelet_ero.distance[-1] - crop_meters)
            i_crop_0 = min(i_crop_0, i_max)
            i_crop_1 = min(i_crop_1, i_max)

            lanelet_ero._left_vertices = lanelet_ero._left_vertices[i_crop_0: -i_crop_1]
            lanelet_ero._center_vertices = lanelet_ero._center_vertices[i_crop_0: -i_crop_1]
            lanelet_ero._right_vertices = lanelet_ero._right_vertices[i_crop_0: -i_crop_1]
        else:
            factor_0 = min(1, crop_meters / lanelet_ero.distance[1])
            lanelet_ero._left_vertices[0] = factor_0 * lanelet_ero._left_vertices[0]\
                                            + (1-factor_0) * lanelet_ero._left_vertices[1]
            lanelet_ero._right_vertices[0] = factor_0 * lanelet_ero._right_vertices[0] \
                                            + (1 - factor_0) * lanelet_ero._right_vertices[1]
            lanelet_ero._center_vertices[0] = factor_0 * lanelet_ero._center_vertices[0] \
                                            + (1 - factor_0) * lanelet_ero._center_vertices[1]

            factor_0 = min(1, crop_meters / (lanelet_ero.distance[-1] - lanelet_ero.distance[-2]))
            lanelet_ero._left_vertices[-1] = factor_0 * lanelet_ero._left_vertices[-2] \
                                            + (1 - factor_0) * lanelet_ero._left_vertices[-1]
            lanelet_ero._right_vertices[-1] = factor_0 * lanelet_ero._right_vertices[-2] \
                                             + (1 - factor_0) * lanelet_ero._right_vertices[-1]
            lanelet_ero._center_vertices[-1] = factor_0 * lanelet_ero._center_vertices[-2] \
                                              + (1 - factor_0) * lanelet_ero._center_vertices[-1]

        # compute eroded vector from center
        perp_vecs = (lanelet_ero.left_vertices - lanelet_ero.right_vertices) * 0.5
        length = np.linalg.norm(perp_vecs, axis=1)
        factors = np.divide(radius, length)  # 0.5 * np.ones_like(length))
        factors = np.reshape(factors, newshape=[-1, 1])
        factors = 1 - np.maximum(factors, np.ones_like(factors) * min_factor) # ensure minimum width of eroded lanelet
        perp_vec_ero = np.multiply(perp_vecs, factors)

        # recompute vertices
        lanelet_ero._left_vertices = lanelet_ero.center_vertices + perp_vec_ero
        lanelet_ero._right_vertices = lanelet_ero.center_vertices - perp_vec_ero
        if lanelet_ero._polygon is not None:
            lanelet_ero._polygon = Polygon(np.concatenate((lanelet_ero.right_vertices,
                                                           np.flip(lanelet_ero.left_vertices, 0))))
        lanelets_ero.append(lanelet_ero)

    return LaneletNetwork.create_from_lanelet_list(lanelets_ero)
