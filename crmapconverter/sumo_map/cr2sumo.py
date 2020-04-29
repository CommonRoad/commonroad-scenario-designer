"""
This class contains functions for converting a CommonRoad map into a .net.xml SUMO map
"""

import itertools
import os
import random
import subprocess
from typing import Type
from xml.etree import cElementTree as ET
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


class CR2SumoMapConverter:
    """Converts CommonRoad map to sumo map .net.xml"""
    def __init__(self, lanelet_network:LaneletNetwork, conf:Type[CR2SumoNetConfig] = CR2SumoNetConfig):
        """

        :param scenario: CommonRoad scenario to be converted
        :param conf: configuration file for additional map conversion parameters
        """
        self.lanelet_network = None
        self.lanelet_network = lanelet_network
        self.conf = conf

        self.nodes = {}  # all the nodes of the map, key is the node ID
        self.edges = {}  # all the edges of the map, key is the edge ID
        self.points_dict = {}  # dictionary for the shape of the edges
        self.connections = {}  # all the connections of the map
        self.lanes_dict = {}  # key is the ID of the edges and value the ID of the lanelets that compose it
        self.explored_lanelets = []  # list of the already explored lanelets
        # globals because used more than one time
        self.edge_priority = 1
        self.edge_function = 'normal'
        self.max_vehicle_width = max(self.conf.veh_params['width'].values())

    @classmethod
    def from_file(cls, file_path_cr, conf: Type[CR2SumoNetConfig] = CR2SumoNetConfig):
        scenario, _ = CommonRoadFileReader(file_path_cr).open()
        return cls(scenario.lanelet_network, conf)

    def _create_shapes(self):
        """
        Create a dictionary containing the shapes of all the lanelets in the network
        :return: nothing
        """
        for lanelet in self.lanelet_network.lanelets:
            self.points_dict.update({lanelet.lanelet_id: lanelet.center_vertices})

    def convert_net(self):
        """
        Convert a CommonRoad net into a SUMO net
        sumo_net contains the converted net
        points_dict contains the shape of the edges
        :return: sumo_net, points_dict
        """
        node_id = 0  # running node_id, will be increased for every new node
        #The shape are needed from the beginning
        self._create_shapes()

        # plt.figure(figsize=[25,25])
        # draw_object(self.lanelet_network, draw_params={'lanelet':{'show_label':True}})
        # plt.draw()
        # plt.autoscale()
        # plt.ion()
        # plt.axis('equal')
        # plt.pause(0.001)

        for lanelet in self.lanelet_network.lanelets:
            # find all lanelets belonging to an edge
            lanelet_width = self._calculate_lanelet_width_from_cr(lanelet)
            edge_id = lanelet.lanelet_id
            successors = lanelet.successor

            self.connections.update({edge_id: successors})
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
            while adj_right_id is not None and right_same_direction is not False:
                self.explored_lanelets.append(adj_right_id)
                # Get start and end nodes of right adjacency.
                right_lanelet = self.lanelet_network.find_lanelet_by_id(adj_right_id)
                adj_right_id = right_lanelet._adj_right
                right_same_direction = right_lanelet.adj_right_same_direction
                adj_right_start = right_lanelet.center_vertices[0]
                start_node_list.append(adj_right_start)
                adj_right_end = right_lanelet.center_vertices[-1]
                end_node_list.append(adj_right_end)
                lanelets.append(right_lanelet)
                rightmost_lanelet = right_lanelet

            # find leftmost lanelet
            while adj_left_id is not None and left_same_direction is not False:
                self.explored_lanelets.append(adj_left_id)
                # Get start and end nodes of left adjacency.
                left_lanelet = self.lanelet_network.find_lanelet_by_id(adj_left_id)
                adj_left_id = left_lanelet._adj_left
                left_same_direction = left_lanelet.adj_left_same_direction
                adj_left_start = left_lanelet.center_vertices[0]
                start_node_list.append(adj_left_start)
                adj_left_end = left_lanelet.center_vertices[-1]
                end_node_list.append(adj_left_end)
                lanelets.append(left_lanelet)

            # creation of the start and end nodes
            # start node
            node_type = 'right_before_left'
            toAdd = True
            for key, node_temp in self.nodes.items():
                temp_coord = np.array(node_temp.getCoord())
                # if tempx == node_x and tempy == node_y:
                for node in start_node_list:
                    # if (temp_coord == node).all():
                    if np.max(np.abs((temp_coord - node))) <= (lanelet_width + 1.0):
                        toAdd = False
                        nodeA = node_temp
                        break

            if toAdd:
                start_node = Node(node_id, node_type, start_node_coordinates, [])
                self.nodes.update({str(node_id): start_node})
                nodeA = start_node
                node_id += 1

            # end node
            toAdd = True
            for key, node_temp in self.nodes.items():
                temp_coord = node_temp.getCoord()
                tempx = temp_coord[0]
                tempy = temp_coord[1]
                temp_coord = np.array([tempx,tempy])
                for node in end_node_list:
                    if np.max(np.abs((temp_coord - node))) <= (lanelet_width + 1.0):
                        toAdd = False
                        nodeB = node_temp
                        break

            if toAdd:
                end_node = Node(node_id, node_type, end_node_coordinates, [])
                self.nodes.update({str(node_id): end_node})
                nodeB = end_node
                node_id += 1

            # calculation of the length of a lane, lanes that belong to the same edge have the same length
            length = np.min([lanelet.distance[-1] for lanelet in lanelets])

            # Creation of Edge, using id as name
            edge = Edge(id=edge_id, fromN=nodeA, toN=nodeB, prio=self.edge_priority, function=self.edge_function,
                        name=edge_id)
            self.edges.update({str(edge_id): edge})
            if self.conf.overwrite_speed_limit is not None:
                speed_limit = self.conf.overwrite_speed_limit
            else:
                speed_limit = lanelet.speed_limit
                if (speed_limit == float('inf')):
                    speed_limit = self.conf.unrestricted_speed_limit_default

            # #right most lane must be the first
            # if right_same_direction and right_same_direction not in self.explored_lanelets:
            #     shape = self.points_dict.get(adj_right_id)
            #     Lane(edge, speed_limit, length, width=lanelet_width, allow=None, disallow=None, shape=shape)
            #     lanes.append(adj_right_id)
            #
            # # creation of a lane, every edge by default must have at least one lane
            # Lane(edge, speed_limit, length, width=lanelet_width, allow=None, disallow=None, shape=center_vertices)
            # lanes.append(edge_id)

            # order lanelets
            ordered_lanelet_ids = [rightmost_lanelet.lanelet_id]
            while len(lanelets) != len(ordered_lanelet_ids):
                ordered_lanelet_ids.append(rightmost_lanelet.adj_left)
                rightmost_lanelet = self.lanelet_network.find_lanelet_by_id(ordered_lanelet_ids[-1])

            # creation of an additional lane if there is a left adjacent lanelet
            for lanelet_id in ordered_lanelet_ids:
                shape = self.points_dict.get(lanelet_id)
                max_curvature = compute_max_curvature_from_polyline(shape)
                # if lanelet_width <= self.max_vehicle_width:
                #     raise ValueError(
                #         "The lanelet width {} meters on lanelet {} is smaller than the allowed maximum vehicle width {} meters!".format(
                #             lanelet_width, lanelet_id, self.max_vehicle_width))
                disallow = self._filter_disallowed_vehicle_classes(max_curvature, lanelet_width, lanelet_id)

                Lane(edge, speed_limit, length, width=lanelet_width, allow=None, disallow=disallow, shape=shape)

            self.lanes_dict.update({edge_id: ordered_lanelet_ids})

        # simplification steps
        # self._merge_junctions(self.conf.max_node_distance)
        self._merge_junction_clustering(self.conf.max_node_distance)
        self._filter_edges()
        # self._simplify_connections_new()
        self._create_lane_based_connections()
        # self._detect_zippers(self.merged_dictionary)
        # self._simplify_connections()
        #self.simplified_connections = self.connections

        # getting the parameters that will be returned
        number_of_junctions = self._calculate_number_junctions()
        speeds_list = self._get_speeds_list()

        # return self.points_dict, total_lanes_length, number_of_junctions, speeds_list

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

    # self._detect_zipper

    def _filter_edges(self):
        """
        Remove edges that lie inside a junction. Those will be replaced by internal edges
        :return: nothing
        """
        for edge in self.edges.values():
            removeEdge = self._consider_edge(edge)
            if removeEdge:
                continue
            edge_id = edge.getID()
            start = edge.getFromNode()
            start_id = start.getID()
            end = edge.getToNode()
            end_id = end.getID()
            flagStart = False
            flagEnd = False
            for new_node, merged_nodes in self.merged_dictionary.items():
                ids_list = []
                for node in merged_nodes:
                    ids_list.append(node.getID())
                if start_id in ids_list:
                    newStart = new_node
                    flagStart = True
                if end_id in ids_list:
                    newEnd = new_node
                    flagEnd = True

            # if only the starting node changed
            if flagStart and not flagEnd:
                edge.setFrom(newStart)
            # if only the ending node changed
            if not flagStart and flagEnd:
                edge.setTo(newEnd)
            # if bothe nodes changed
            if flagStart and flagEnd:
                edge.setFrom(newStart)
                edge.setTo(newEnd)
            self.new_edges.update({edge_id: edge})

    def _consider_edge(self, edge):
        """
        returns True if the edge must be removed, False otherwise
        :param edge: the edge to consider
        :return: flag removeEdge
        """
        removeEdge = False
        startNode = edge.getFromNode()
        endNode = edge.getToNode()
        startNodeID = startNode.getID()
        endNodeID = endNode.getID()

        for key, value in self.merged_dictionary.items():
            listIDs = []
            for node in value:
                listIDs.append(node.getID())
            if startNodeID in listIDs and endNodeID in listIDs:
                removeEdge = True

        return removeEdge

    # def _simplify_connections(self):
    #     """
    #     Instantiate a new dictionary with only the connections that are meaningful after the simplification of the net
    #     :return: nothing
    #     """
    #     self.simplified_connections = {}
    #     for keyEdge, connections in self.connections.items():
    #         toEdges = []
    #         for connection in connections:
    #             next = self.connections[connection]
    #             toEdges = toEdges + next
    #         fromEdgeNew, toEdgesNew = self._redefine_connection(keyEdge, toEdges)
    #         mustAdd = self._check_addition(toEdgesNew)
    #         alreadyUpdated = False
    #         if len(toEdges) != 0 and mustAdd and fromEdgeNew in self.new_edges.keys():
    #             if fromEdgeNew in self.simplified_connections.keys():
    #                 toUpdate = self.simplified_connections.get(fromEdgeNew)
    #                 toUpdate = toUpdate + toEdgesNew
    #                 self.simplified_connections.update({fromEdgeNew: toUpdate})
    #                 alreadyUpdated = True
    #             if alreadyUpdated is False:
    #                 self.simplified_connections.update({fromEdgeNew: toEdgesNew})

    def _check_addition(self, toEdges):
        """
        Check if the connection is really to add
        :param toEdges: destination edges to check
        :return: True if the connection must be added, False otherwise
        """
        mustAdd = True
        for connection in toEdges:
            if connection not in self.new_edges.keys():
                mustAdd = False
        return mustAdd

    def _redefine_connection(self, fromEdge, toEdges):
        """
        Substitute the ID of edges that were transformed into lanes with their corresponding edge ID
        :param fromEdge: source Edge ID
        :param toEdges: destinations edges IDs
        :return: fromEdgeNew, toEdgesNew
        """
        toEdgesNew = []
        for mastereEdge, lanes in self.lanes_dict.items():
            if fromEdge in lanes:
                fromEdgeNew = mastereEdge
            for edge in toEdges:
                if edge in lanes:
                    toEdgesNew.append(mastereEdge)
        return fromEdgeNew, toEdgesNew

    def _create_lane_based_connections(self):
        """
        Instantiate a new dictionary with only the connections that are meaningful after the simplification of the net
        :return: nothing
        """
        self.simplified_connections = {}
        self.connection_shapes = {}
        new_lane_ids = set(itertools.chain.from_iterable([self.lanes_dict[edg] for edg in self.new_edges]))
        # print(self.connections)
        for keyEdge, connections in self.connections.items():
            if keyEdge not in new_lane_ids:
                continue
            explored_edges = set()
            queue = [[via] for via in connections]  # list with edge ids to toLane
            paths = []
            # queue = set(copy.deepcopy(connections))
            # expand successor until non-internal (i.e. not in merged_nodes_all) edge is found
            while queue:
                # print(queue)
                current_path = queue.pop()
                succ_edge = current_path[-1]
                explored_edges.add(succ_edge)
                if succ_edge not in new_lane_ids:
                    for next_edge in self.connections[succ_edge]:
                        if next_edge not in explored_edges:
                            queue.append(current_path + [next_edge])
                else:
                    paths.append(current_path)

            # judge whether detailed lane id should be defined
            toEdges = [path[-1] for path in paths]
            shapes = []
            for path in paths:
                shapes.append(np.vstack([self.points_dict[lanelet_id] for lanelet_id in path]))

            fromEdgeNew, toEdgesNew = self._redifine_connection_new(keyEdge, toEdges) #25_1, [24_0]
            # mustAdd = self._check_addition_new([pair[1] for pair in via_successors])
            alreadyUpdated = False
            if len(toEdgesNew) != 0 and int(fromEdgeNew.split("_")[0]) in self.new_edges.keys():
                if fromEdgeNew.split("_")[0] in self.simplified_connections.keys():
                    toUpdate = self.simplified_connections.get(fromEdgeNew)
                    toUpdate = toUpdate + toEdgesNew
                    self.simplified_connections.update({fromEdgeNew: toUpdate})
                    for edge, shape in zip(toEdgesNew, shapes):
                        self.connection_shapes.update({(fromEdgeNew, edge): shape})
                    alreadyUpdated = True
                if alreadyUpdated is False:
                    self.simplified_connections.update({fromEdgeNew: toEdgesNew})
                    for edge, shape in zip(toEdgesNew, shapes):
                        self.connection_shapes.update({(fromEdgeNew,edge): shape})

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

    def write_net(self, output_path):
        """
        Function for writing the edges and nodes files in xml format
        :param output_path: the relative path of the output
        :return: nothing
        """
        self._writeEdgesFile(output_path)
        self._write_nodes_file(output_path)
        self._write_connections_file(output_path)

    def write_net_new(self, output_path):
        """
        Function for writing the edges and nodes files in xml format
        :param output_path: the relative path of the output
        :return: nothing
        """
        self._writeEdgesFile(output_path)
        self._write_nodes_file(output_path)
        self._write_connections_file_new(output_path)

    def _writeEdgesFile(self, output_path):
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
            for from_id, successors in self.simplified_connections.items():
                for successor in successors:
                    connection = ET.SubElement(connections, 'connection')
                    connection.set('from', str(from_id.split('_')[0]))
                    connection.set('to', str(successor.split('_')[0]))
                    connection.set('fromLane', str(from_id.split('_')[1]))
                    connection.set('toLane', str(successor.split('_')[1]))
                    connection.set('contPos', str(-4.0))  # defines waiting position of vehicles at left turns in internal junctions
                    # if (from_id, successor) in self.connection_shapes:
                    #     connection.set('shape', self._getShapeString(self.connection_shapes[(from_id, successor)]))
                        # connection.set('via', str(pair[0]))
            output_str = ET.tostring(connections, encoding='utf8', method='xml').decode("utf-8")
            reparsed = minidom.parseString(output_str)
            output_file.write(reparsed.toprettyxml(indent="\t"))

    @staticmethod
    def merge_files(output_path:str, cleanup=False) -> bool:
        """
        Function that merges the edges and nodes files into one using netconvert
        :param output_path: the relative path of the output
        :param cleanup: deletes input files after creating net file
        :return: bool: returns False if conversion fails
        """
        # The header of the xml files must be removed
        toRemove = ["options", "xml"]

        # Removing header in edges file
        with open(os.path.join(os.path.dirname(output_path), '_edges.net.xml'), 'r') as file:
            lines = file.readlines()
        with open(os.path.join(os.path.dirname(output_path), '_edges.net.xml'), 'w') as file:
            for line in lines:
                if not any(word in line for word in toRemove):
                    file.write(line)

        # Removing header in nodes file
        with open(os.path.join(os.path.dirname(output_path), '_nodes.net.xml'), 'r') as file:
            lines = file.readlines()
        with open(os.path.join(os.path.dirname(output_path), '_nodes.net.xml'), 'w') as file:
            for line in lines:
                if not any(word in line for word in toRemove):
                    file.write(line)

        # Removing header in connections file
        with open(os.path.join(os.path.dirname(output_path), '_connections.net.xml'), 'r') as file:
            lines = file.readlines()
        with open(os.path.join(os.path.dirname(output_path), '_connections.net.xml'), 'w') as file:
            for line in lines:
                if not any(word in line for word in toRemove):
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
                      "--offset.disable-normalization=false " \
                      "--node-files=" + str(nodesFile) + \
                      " --edge-files=" + str(edgesFile) + \
                      " --connection-files=" + str(connectionsFile) + \
                      " --output-file=" + str(output)
        # "--geometry.remove.keep-edges.explicit " \
        # "--junctions.limit-turn-speed=6.5 " \
        # "--geometry.max-segment-length=15 " \
        success = True
        try:
            _ = subprocess.check_output(bashCommand.split(), timeout=5.0)
        except:
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

    def convert_to_cr(self, output_file:str):
        """Convert the Commonroad scenario to a net.xml file, specified by the absolute  path output_file."""
        self.convert_net()
        self.write_net(output_file)
        self.merge_files(output_file)