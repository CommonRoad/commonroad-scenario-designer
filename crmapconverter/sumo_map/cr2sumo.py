"""
This class contains functions for converting a CommonRoad map into a .net.xml SUMO map
"""
import logging
import os
import random
import subprocess
import warnings
from collections import defaultdict
from copy import copy, deepcopy
from typing import Dict, List, Set, Tuple
from xml.dom import minidom
from xml.etree import cElementTree as ET

import numpy as np
import sumolib
from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.util import Interval
from commonroad.scenario.lanelet import Lanelet, LaneletNetwork
from commonroad.scenario.traffic_sign import (SupportedTrafficSignCountry,
                                              TrafficLight,
                                              TrafficLightCycleElement,
                                              TrafficLightDirection)
from commonroad.scenario.traffic_sign_interpreter import TrafficSigInterpreter
from commonroad.visualization.draw_dispatch_cr import draw_object
from matplotlib import pyplot as plt
from sumocr.maps.scenario_wrapper import AbstractScenarioWrapper

from .config import (SumoConfig, lanelet_type_CR2SUMO,
                     traffic_light_states_CR2SUMO,
                     traffic_light_states_SUMO2CR)
from .sumolib_net import (TLS, Connection, Crossing, Edge, Junction, Lane,
                          Node, TLSProgram)
from .sumolib_net.lane import SUMO_VEHICLE_CLASSES
from .util import (_find_intersecting_edges,
                   compute_max_curvature_from_polyline, vector_angle,
                   edge_centroid, get_scenario_name_from_netfile,
                   get_total_lane_length_from_netfile, max_lanelet_network_id,
                   merge_crossings, min_cluster,
                   remove_unreferenced_traffic_lights,
                   write_ego_ids_to_rou_file, intersect_lanelets_line, orthogonal_ccw_vector)

# This file is used as a template for the generated .sumo.cfg files
DEFAULT_CFG_FILE = "default.sumo.cfg"


class CR2SumoMapConverter(AbstractScenarioWrapper):
    """Converts CommonRoad map to sumo map .net.xml"""

    def __init__(
        self,
        lanelet_network: LaneletNetwork,
        conf: SumoConfig,
        country_id: SupportedTrafficSignCountry = SupportedTrafficSignCountry.
            ZAMUNDA):
        """

        :param lanelet_network: lanelet network to be converted
        :param conf: configuration file for additional map conversion parameters
        :param country_id: ID of the country, used to evaluate traffic signs
        """
        self.lanelet_network: LaneletNetwork = lanelet_network
        self.conf: SumoConfig = conf

        # all the nodes of the map, key is the node ID
        self.nodes: Dict[int, Node] = {}
        # all the edges of the map, key is the edge ID
        self.edges: Dict[str, Edge] = {}
        # dictionary for the shape of the edges
        self._points_dict: Dict[int, np.ndarray] = {}
        self._connections = defaultdict(list)  # all the connections of the map
        self._new_connections: List[Connection] = []
        # dict of merged_node_id and Crossing
        self._crossings: Dict[int, List[Crossing]] = dict()
        # key is the ID of the edges and value the ID of the lanelets that compose it
        self.lanes_dict: Dict[int, Tuple[int, ...]] = {}
        self.lanes: Dict[str, Lane] = {}
        self.edge_lengths = {}
        # list of the already explored lanelets
        self._explored_lanelets = []
        self._max_vehicle_width = max(self.conf.veh_params['width'].values())
        self._trafic_sign_interpreter: TrafficSigInterpreter = TrafficSigInterpreter(
            country_id, self.lanelet_network)
        self.lane_id2lanelet_id: Dict[str, int] = {}
        self.lanelet_id2lane_id: Dict[int, str] = {}
        self.lanelet_id2edge_id: Dict[int, int] = {}
        # generated junctions by NETCONVERT
        self.lanelet_id2junction: Dict[int, Junction] = {}
        self._start_nodes = {}
        self._end_nodes = {}
        # tl (traffic_light_id) ->  TLS (Traffic Light Signal)
        self.traffic_light_signals: Dict[int, TLS] = {}

        # NETCONVERT files
        self._nodes_file = ""
        self._edges_file = ""
        self._connections_file = ""
        self._tll_file = ""
        self._output_file = ""

        # simulation params
        self.scenario_name = ""
        self.sumo_cfg_file = ""
        self.ego_start_time = self.conf.ego_start_time

    @classmethod
    def from_file(cls, file_path_cr, conf: SumoConfig):
        scenario, _ = CommonRoadFileReader(file_path_cr).open()
        return cls(scenario.lanelet_network, conf)

    def _convert_map(self):
        self._find_lanes()
        self._init_nodes()
        self._create_sumo_edges_and_lanes()
        self._init_connections()
        self._merge_junctions_intersecting_lanelets()
        self._filter_edges()
        self._create_lane_based_connections()
        self._create_crossings()
        self._create_traffic_lights()

    def _create_traffic_lights(self):

        # tl (traffic_light_id) -> Node (Traffic Light)
        nodes_tl: Dict[int, Node] = {}

        # generate traffic lights in SUMO format
        for lanelet in self.lanelet_network.lanelets:
            lanelet_lights_ids: Set[TrafficLight] = lanelet.traffic_lights
            if not lanelet_lights_ids: continue

            edge_id = self.lanelet_id2edge_id[lanelet.lanelet_id]

            if not edge_id in self.new_edges:
                logging.warning(
                    "Edge: {} has been removed in SUMO-NET but contained a traffic light"
                        .format(edge_id))
                continue

            from_edge: Edge = self.new_edges[edge_id]
            to_node: Node = from_edge.getToNode()
            successor_edges: List[Edge] = [
                edge for id, edge in self.new_edges.items()
                if edge.getFromNode().getID() == to_node.getID()
            ]

            for tl in [
                tl for tl in self.lanelet_network.traffic_lights
                if tl.traffic_light_id in lanelet_lights_ids
            ]:
                # is the traffic light active?
                if not tl.active:
                    logging.info(
                        'Traffic Light: {} is inactive, skipping conversion'.
                            format(tl.traffic_light_id))
                    continue

                ## Only valid if the traffic light has not been created ##

                # create a new node for the traffic light
                traffic_light = Node(
                    self.node_id_next,
                    "traffic_light",
                    # convert TrafficLight position if explicitly given
                    tl.position if tl.position.size > 0 else
                    from_edge.getToNode().getCoord3D(),
                    incLanes=None,
                    tl=tl.traffic_light_id)
                self.node_id_next += 1
                nodes_tl[tl.traffic_light_id] = traffic_light

                # have we already generated the tls for this traffic light?
                if tl.traffic_light_id in self.traffic_light_signals:
                    logging.warning(
                        'TrafficLight: {} is referenced by multiple lanelets'.
                            format(tl.traffic_light_id))
                    continue

                # create Traffic Light Signal
                # give a testing program id:
                tls_program = TLSProgram('cr_converted', tl.time_offset,
                                         'static')
                for cycle in tl.cycle:
                    state = traffic_light_states_CR2SUMO[cycle.state]
                    tls_program.addPhase(state, cycle.duration * self.conf.dt)

                tls = TLS(tl.traffic_light_id)
                tls.addProgram(tls_program)

                def get_lanes(edge) -> List[Lane]:
                    """
                    param: return: List of lanes for the given edge
                    """
                    return [
                        lane for lane_id, lane in self.lanes.items()
                        if edge.getID() == lane.getEdge().getID()
                    ]

                def connection_exists(from_lane: str, to_lane: str) -> bool:
                    """
                    param: return: True iff. a connection between from_lane -> to_lane exists
                    """
                    for c in self._new_connections:
                        if str(c.getFromLane()) == from_lane and str(
                            c.getToLane()) == to_lane:
                            return True
                    return False

                # TODO: Add proper lane modelling for the entire converter
                for to_edge in successor_edges:
                    for from_lane in get_lanes(from_edge):
                        for to_lane in get_lanes(to_edge):
                            if not connection_exists(from_lane.getID(),
                                                     to_lane.getID()):
                                continue
                            tls.addConnection(
                                Connection(from_edge,
                                           to_edge,
                                           from_lane,
                                           to_lane,
                                           direction=None,
                                           tls=tl.traffic_light_id,
                                           tllink=0,
                                           state=None))

                self.traffic_light_signals[tl.traffic_light_id] = tls

        # save nodes to global state
        for tl, node in nodes_tl.items():
            self.new_nodes[node.getID()] = node

    def _find_lanes(self):
        """
        Convert a CommonRoad net into a SUMO net
        sumo_net contains the converted net
        """

        node_id = 0  # running node_id, will be increased for every new node
        self._points_dict = {
            lanelet.lanelet_id: lanelet.center_vertices
            for lanelet in self.lanelet_network.lanelets
        }

        # plt.figure(figsize=[25,25])
        # draw_object(self.lanelet_network, draw_params={'lanelet':{'show_label':True}, 'lanelet_network': {
        #     'intersection': {
        #         'draw_intersections': True}}})
        # plt.draw()
        # plt.autoscale()
        # plt.ion()
        # plt.axis('equal')
        # plt.pause(0.001)
        for lanelet in self.lanelet_network.lanelets:
            edge_id = lanelet.lanelet_id
            successors = set(lanelet.successor)

            # prevent the creation of  multiple edges instead of edges with multiple lanes
            if edge_id in self._explored_lanelets:
                continue

            self._explored_lanelets.append(edge_id)
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
            while adj_right_id and right_same_direction:
                self._explored_lanelets.append(adj_right_id)
                # Get start and end nodes of right adjacency.
                right_lanelet = self.lanelet_network.find_lanelet_by_id(
                    adj_right_id)
                if right_lanelet.successor is not None:
                    if len(
                        successors.intersection(
                            set(right_lanelet.successor))) > 0:
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
            while adj_left_id and left_same_direction:
                self._explored_lanelets.append(adj_left_id)
                # Get start and end nodes of left adjacency.
                left_lanelet = self.lanelet_network.find_lanelet_by_id(
                    adj_left_id)
                if left_lanelet.successor is not None:
                    if len(successors.intersection(set(
                        left_lanelet.successor))) > 0:
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
                current_lanelet = self.lanelet_network.find_lanelet_by_id(
                    ordered_lanelet_ids[-1])

            self.lanes_dict[rightmost_lanelet.lanelet_id] = tuple(
                ordered_lanelet_ids)
            self.edge_lengths[rightmost_lanelet.lanelet_id] = np.min(
                [lanelet.distance[-1] for lanelet in lanelets])

            for i_lane, l_id in enumerate(ordered_lanelet_ids):
                self.lanelet_id2edge_id[l_id] = rightmost_lanelet.lanelet_id

    def _compute_node_coords(self, lanelets, index: int):
        vertices = np.array([l.center_vertices[index] for l in lanelets])
        return np.mean(vertices, axis=0)

    def _create_node(self, edge_id, lanelet_ids: Tuple[int], node_type: str):
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
            if edge_id in self._start_nodes:
                # already assigned to a node, see @REFERENCE_1
                return
        else:
            index = -1
            if edge_id in self._end_nodes:
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
                    [
                        conn_edges.add(self.lanelet_id2edge_id[succ])
                        for succ in conn_lanelet
                    ]

        if len(conn_edges) > 0:
            node_candidates = []
            if node_type == "from":
                node_list_other = self._end_nodes
            else:
                node_list_other = self._start_nodes

            # check if connected edges already have a start/end node
            for to_edg in conn_edges:
                if to_edg in node_list_other:
                    node_candidates.append(node_list_other[to_edg])

            # check: connected edges should already use the same node
            assert len(
                set(node_candidates)) <= 1, 'Unexpected error, please report!'
            if node_candidates:
                # assign existing node
                if node_type == "from":
                    self._start_nodes[edge_id] = node_candidates[0]
                else:
                    self._end_nodes[edge_id] = node_candidates[0]
            else:
                # create new node
                coords = self._compute_node_coords(lanelets, index=index)
                self.nodes[self.node_id_next] = Node(self.node_id_next,
                                                     node_type, coords, [])
                # @REFERENCE_1
                if node_type == "from":
                    self._start_nodes[edge_id] = self.node_id_next
                    for conn_edg in conn_edges:
                        self._end_nodes[conn_edg] = self.node_id_next
                else:
                    self._end_nodes[edge_id] = self.node_id_next
                    for conn_edg in conn_edges:
                        self._start_nodes[conn_edg] = self.node_id_next

                self.node_id_next += 1
        else:
            # dead end
            coords = self._compute_node_coords(lanelets, index=index)
            self.nodes[self.node_id_next] = Node(self.node_id_next, node_type,
                                                 coords, [])
            if node_type == "from":
                self._start_nodes[edge_id] = self.node_id_next
            else:
                self._end_nodes[edge_id] = self.node_id_next

            self.node_id_next += 1

    def _init_nodes(self):
        # creation of the start and end nodes
        # start node
        self.node_id_next = 1
        self._start_nodes = {
        }  # contains start nodes of each edge{edge_id: node_id}
        self._end_nodes = {
        }  # contains end nodes of each edge{edge_id: node_id}
        for edge_id, lanelet_ids in self.lanes_dict.items():
            self._create_node(edge_id, lanelet_ids, 'from')
            self._create_node(edge_id, lanelet_ids, 'to')

    def _create_sumo_edges_and_lanes(self):
        """
        Creates edges for net file with previously collected edges and nodes.
        :return:
        """

        for edge_id, lanelet_ids in self.lanes_dict.items():
            # Creation of Edge, using id as name
            start_node = self.nodes[self._start_nodes[edge_id]]
            end_node = self.nodes[self._end_nodes[edge_id]]
            # TODO: create priority from right of way rule in CR file
            edge = Edge(id=edge_id,
                        fromN=start_node,
                        toN=end_node,
                        prio=1,
                        function='normal',
                        name=edge_id)
            self.edges.update({str(edge_id): edge})
            if self.conf.overwrite_speed_limit is not None:
                speed_limit = self.conf.overwrite_speed_limit
            else:
                speed_limit = self._trafic_sign_interpreter.speed_limit(
                    frozenset([lanelet.lanelet_id]))
                if speed_limit is None or np.isinf(speed_limit):
                    speed_limit = self.conf.unrestricted_speed_limit_default

            for lanelet_id in lanelet_ids:
                shape = self._points_dict.get(lanelet_id)
                lanelet = self.lanelet_network.find_lanelet_by_id(lanelet_id)
                lanelet_width = self._calculate_lanelet_width_from_cr(lanelet)
                max_curvature = compute_max_curvature_from_polyline(shape)
                # if lanelet_width <= self._max_vehicle_width:
                #     raise ValueError(
                #         "The lanelet width {} meters on lanelet {} is smaller than the allowed maximum vehicle width {} meters!".format(
                #             lanelet_width, lanelet_id, self._max_vehicle_width))
                disallow = self._filter_disallowed_vehicle_classes(
                    max_curvature, lanelet_width, lanelet_id)
                allow = set([
                    t for tpe in lanelet.lanelet_type
                    for t in lanelet_type_CR2SUMO[tpe]
                ])
                allow = allow if len(
                    allow) > 0 else set(SUMO_VEHICLE_CLASSES) - set(disallow)

                lane = Lane(edge,
                            speed_limit,
                            self.edge_lengths[edge_id],
                            width=lanelet_width,
                            allow=allow,
                            shape=shape)
                self.lanes[lane.getID()] = lane
                self.lane_id2lanelet_id[lane.getID()] = lanelet_id
                self.lanelet_id2lane_id[lanelet_id] = lane.getID()

        # set oncoming lanes
        for edge_id, lanelet_ids in self.lanes_dict.items():
            leftmost_lanelet = self.lanelet_network.find_lanelet_by_id(
                lanelet_ids[-1])
            if leftmost_lanelet.adj_left is not None:
                self.lanes[self.lanelet_id2lane_id[lanelet_ids[-1]]] \
                    .setAdjacentOpposite(self.lanelet_id2lane_id[leftmost_lanelet.adj_left])

    def _init_connections(self):
        """
        Init connections, doesn't consider junctions yet.
        :return:
        """
        for l in self.lanelet_network.lanelets:
            if l.successor:
                self._connections[self.lanelet_id2lane_id[
                    l.lanelet_id]].extend([
                    self.lanelet_id2lane_id[succ] for succ in l.successor
                ])

    def _filter_disallowed_vehicle_classes(self, max_curvature: float,
                                           lanelet_width, lanelet_id) -> str:
        """
        Filter out the vehicle classes which should be disallowed on a specific lanelet due to large curvature.
        :param max_curvature: maximum curvature of the lanelet
        :param lanelet_width: width of the lanelet
        :param lanelet_id:
        :return: string of disallowed classes
        """

        # select the disallowed vehicle classes
        disallow = []

        if max_curvature > 0.001:  # not straight lanelet
            radius = 1 / max_curvature
            max_vehicle_length_sq = 4 * (
                (radius + lanelet_width / 2) ** 2 -
                (radius + self._max_vehicle_width / 2) ** 2)

            for veh_class, veh_length in self.conf.veh_params['length'].items(
            ):
                # only disallow vehicles longer than car (class passenger)
                if veh_length ** 2 > max_vehicle_length_sq and veh_length > self.conf.veh_params[
                    'length']['passenger']:
                    disallow.append(veh_class)
                    # print("{} disallowed on lanelet {}, allowed max_vehicle_length={}".format(veh_class, lanelet_id,
                    #                                                                           max_vehicle_length))
        return disallow

    @staticmethod
    def _calculate_lanelet_width_from_cr(lanelet):
        """
        Calculate the average width of a lanelet.
        :param lanelet: the lane whose width is to be calculated
        :return: average_width
        """
        helper_matrix = lanelet.right_vertices - lanelet.left_vertices
        distance_array = helper_matrix[:, 0] ** 2 + helper_matrix[:, 1] ** 2
        average_width = np.sqrt(np.min(distance_array))
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
        speeds_list = []  # list of speed that will be returned by the method
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

    def _merge_junctions_intersecting_lanelets(self):
        """
        Merge nodes when their connecting edges intersect.
        :return:
        """
        # new dictionary for the merged nodes
        self.new_nodes = self.nodes.copy()
        # new dictionary for the edges after the simplifications
        self.new_edges = {}
        # key is the merged node, value is a list of the nodes that form the merged node
        self.merged_dictionary = {}
        self.replaced_nodes = defaultdict(list)

        # merged node clustering
        clusters: Dict[int, Set[Node]] = defaultdict(set)
        next_cluster_id = 0
        # crossings are additional info for a cluster
        clusters_crossing: Dict[int, Crossing] = dict()
        # Merge Lanelets lying in the same CR intersection
        # merging based on specified Lanelets in intersection
        for intersection in self.lanelet_network.intersections:
            intersecting_lanelets = {
                lanelet_id
                for incoming in intersection.incomings
                for lanelet_id in incoming.successors_right
                                  | incoming.successors_left
                                  | incoming.successors_straight
            }
            intersecting = intersecting_lanelets | intersection.crossings
            edges = {
                str(self.lanelet_id2edge_id[step])
                for step in intersecting
            }
            merged_nodes = {
                node
                for e_id in edges for node in
                [self.edges[e_id].getFromNode(), self.edges[e_id].getToNode()]
            }
            clusters[next_cluster_id] = merged_nodes

            # generate partial Crossings
            crossings = []
            for lanelet_id in intersection.crossings:
                lanelet = self.lanelet_network.find_lanelet_by_id(lanelet_id)
                crossings.append(
                    Crossing(node=None,
                             edges=None,
                             shape=lanelet.center_vertices,
                             width=3.0))
            if crossings:
                clusters_crossing[next_cluster_id] = crossings

            next_cluster_id += 1

        # Expand merged clusters by all lanelets intersecting each other.
        # merging based on Lanelets intersecting each other
        intersecting_pairs = _find_intersecting_edges(self.lanes_dict,
                                                      self.lanelet_network)
        intersecting_edges = defaultdict(set)
        for pair in intersecting_pairs:
            intersecting_edges[pair[0]].add(pair[1])
            intersecting_edges[pair[1]].add(pair[0])

        explored_nodes = set()
        for node_id, current_node in self.nodes.items():
            if current_node in explored_nodes:
                continue
            merged_nodes = {current_node}
            queue = [current_node]

            current_cluster_id = next(
                (cluster_id for cluster_id, cluster in clusters.items()
                 if current_node in cluster), None)
            current_cluster = clusters[current_cluster_id]
            # delete current_cluster from dict
            if current_cluster:
                merged_nodes = current_cluster
                clusters[current_cluster_id] = set()
            # expand current cluster of intersecting lanelets
            while len(queue) > 0:
                expanded_node = queue.pop()
                if expanded_node in explored_nodes: continue
                explored_nodes.add(expanded_node)

                incomings = {e.getID() for e in expanded_node.getIncoming()}
                outgoings = {e.getID() for e in expanded_node.getOutgoing()}

                for inc_edg in incomings:
                    for intersecting_inc in intersecting_edges[inc_edg]:
                        from_node: Node = self.edges[str(
                            intersecting_inc)].getFromNode()
                        if from_node.getID() in {
                            node.getID()
                            for cluster in clusters.values()
                            for node in cluster
                        }:
                            continue
                        merged_nodes.add(from_node)
                        queue.append(from_node)

                for out_edg in outgoings:
                    for intersecting_out in intersecting_edges[out_edg]:
                        to_node = self.edges[str(intersecting_out)].getToNode()
                        if to_node.getID() in {
                            node.getID()
                            for cluster in clusters.values()
                            for node in cluster
                        }:
                            continue
                        merged_nodes.add(to_node)
                        queue.append(to_node)

            clusters[current_cluster_id] = merged_nodes

        # only merge if we found more than one node to merge
        clusters = {
            id: cluster
            for id, cluster in clusters.items() if len(cluster) > 1
        }

        for cluster_id, cluster in clusters.items():
            logging.info(f"Merging nodes: {[n.getID() for n in cluster]}")
            # create new merged node
            merged_node = Node(id=self.node_id_next,
                               node_type='priority',
                               coord=self._calculate_centroid(cluster),
                               incLanes=[])
            self.node_id_next += 1
            self.new_nodes[merged_node.getID()] = merged_node
            cluster = {n.getID() for n in cluster}
            for old_node in cluster:
                assert not old_node in self.replaced_nodes
                self.replaced_nodes[old_node].append(merged_node.getID())
            self.merged_dictionary[merged_node.getID()] = cluster

            # provide full definition of every crossing. Then make globally available
            if cluster_id in clusters_crossing:
                crossings = clusters_crossing[cluster_id]
                for crossing in crossings:
                    crossing.node = merged_node
                self._crossings[merged_node.getID()] = crossings

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
                    merged_nodes |= self.merged_dictionary[new_node_tmp]
                    for merged_node in self.merged_dictionary[new_node_tmp]:
                        if len(self.replaced_nodes[merged_node]) > 1:
                            new_candidates = list(
                                set(new_candidates +
                                    self.replaced_nodes[merged_node]).
                                    difference(explored_candidates))

                for node_id in explored_candidates:
                    del self.merged_dictionary[node_id]
                    if node_id != new_node:
                        del self.new_nodes[node_id]

                self.merged_dictionary[new_node] = merged_nodes
                explored_nodes_all |= merged_nodes
                for merged_node in merged_nodes:
                    self.replaced_nodes[merged_node] = [new_node]

    def _filter_edges(self):
        """
        Remove edges that lie inside a junction. Those will be replaced by internal edges
        :return: nothing
        """
        # self.new_edges = {e.getID():e for e in self.edges.values()}
        for edge in self.edges.values():
            if self._is_merged_edge(edge):
                continue

            edge_id = edge.getID()
            start_id = edge.getFromNode().getID()
            end_id = edge.getToNode().getID()

            # update merged edges to from/to the merged node
            for new_node_id, merged_nodes in self.merged_dictionary.items():
                if start_id in merged_nodes:
                    edge.setFrom(self.new_nodes[new_node_id])
                    break

            for new_node_id, merged_nodes in self.merged_dictionary.items():
                if end_id in merged_nodes:
                    edge.setTo(self.new_nodes[new_node_id])
                    break

            self.new_edges[edge_id] = edge

    def _create_lane_based_connections(self):
        """
        Instantiate a new dictionary with only the connections that are meaningful after the simplification of the net
        :return: nothing
        """
        edge_ids = [str(edge.getID()) for edge in self.new_edges.values()]
        for from_lane, connections in self._connections.copy().items():
            if from_lane.split("_")[0] not in edge_ids:
                continue
            explored_lanes = set()
            queue = [[via]
                     for via in connections]  # list with edge ids to toLane
            paths = []
            # explore paths
            while queue:
                current_path = queue.pop()
                succ_lane = current_path[-1]
                explored_lanes.add(succ_lane)
                if succ_lane.split("_")[0] not in edge_ids:
                    for next_lane in self._connections[succ_lane]:
                        if next_lane not in explored_lanes:
                            queue.append(current_path + [next_lane])
                else:
                    paths.append(current_path)

            for path in paths:
                if len(path) > 1:
                    shape = np.vstack([
                        self._points_dict[self.lane_id2lanelet_id[lane_id]]
                        for lane_id in path[:-1]
                    ])
                    via = path[1]
                else:
                    shape = None
                    via = None
                connection = Connection(
                    fromEdge=from_lane.split("_")[0],
                    toEdge=path[-1].split("_")[0],
                    fromLane=int(from_lane.split("_")[-1]),
                    toLane=int(path[-1].split("_")[-1]),
                    viaLaneID=via,
                    shape=self._getShapeString(shape)
                    if shape is not None else None,
                    keepClear=True,
                    contPos=self.conf.wait_pos_internal_junctions)
                self._new_connections.append(connection)

    def _create_crossings(self):
        new_crossings = dict()
        for merged_node_id, crossings in self._crossings.items():
            merged_node = self.new_nodes[merged_node_id]
            adjacent_edges = {
                edge
                for edge in self.new_edges.values()
                if edge.getToNode() == merged_node
                   or edge.getFromNode() == merged_node
            }
            pedestrian_edges = {
                edge
                for edge in adjacent_edges if all([
                    "pedestrian" in lane.getAllowed()
                    for lane in edge.getLanes()
                ])
            }
            non_pedestrian_edges = adjacent_edges - pedestrian_edges

            if not non_pedestrian_edges:
                continue

            clusters = min_cluster(
                non_pedestrian_edges, lambda dist: dist < 4,
                lambda e1, e2: max(
                    np.linalg.norm(
                        np.array(e1.getFromNode().getCoord()) - np.array(
                            e2.getToNode().getCoord())),
                    np.linalg.norm(
                        np.array(e1.getToNode().getCoord()) - np.array(
                            e2.getFromNode().getCoord()))))
            merged_crossings = merge_crossings(crossings)

            # filter all crossings close to parallel to any of the clusters
            # if we have more than merged crossing
            # min angle: PI/4
            merged_crossings = [
                c for c in merged_crossings if np.min([
                    vector_angle(
                        np.array(e.getToNode().getCoord()) -
                        np.array(e.getFromNode().getCoord()), c.shape[-1] -
                        c.shape[0]) for cluster in clusters for e in cluster
                ]) > np.pi / 4
            ] if len(merged_crossings) > 1 else merged_crossings
            # choose the crossing with maximal length
            crossing = merged_crossings[np.argmax([
                np.linalg.norm(m.shape[-1] - m.shape[0])
                for m in merged_crossings
            ])]
            crossing.shape = intersect_lanelets_line(
                {
                    self.lanelet_network.find_lanelet_by_id(l_id)
                    for l_id, e_id in self.lanelet_id2edge_id.items()
                    if e_id in
                       {edge.getID()
                        for cluster in clusters for edge in cluster}
                }, crossing.shape)

            # assign each cluster the same crossing shape
            split_crossings = []
            for cluster in clusters:
                c = copy(crossing)

                def compute_edge_angle(e: Edge, pivot: np.ndarray) -> float:
                    """computes angle between edge and the x axis, when moved into the pivot"""
                    center = edge_centroid(e)
                    return np.arctan2(-(center[1] - pivot[1]),
                                      -(center[0] - pivot[0]))

                # order edges in counter-clock-wise direction
                c.edges = sorted(
                    cluster, key=lambda edge: compute_edge_angle(edge, c.shape[0])
                )
                logging.info(
                    f"ordered edges ccw direction {[e.getID() for e in cluster]} -> {[e.getID() for e in c.edges]}"
                )

                # Assure that c.shape is in counter clockwise direction within the junction
                # Move c.shape to the centroid of it's edges, them make sure it is in ccw direction
                edge_ends = np.array(
                    [node.getCoord() for edge in c.edges for node in [edge.getFromNode(), edge.getToNode()]]
                )
                edge_centre = np.mean(edge_ends, axis=0)
                crossing_centre = np.mean(c.shape, axis=0)
                junction_centre = edge_ends[np.argmin(np.linalg.norm(edge_ends - crossing_centre, axis=1))]
                orthogonal = orthogonal_ccw_vector(junction_centre, edge_centre)
                centered_crossing = c.shape + (edge_centre - crossing_centre)
                # is the centered crossing going the same direction as the ccw vector
                # if not flip it's elements
                if np.dot(orthogonal, centered_crossing[-1] - centered_crossing[0]) < 0:
                    c.shape = np.flip(c.shape, axis=0)
                split_crossings.append(c)

            new_crossings[merged_node_id] = split_crossings
        self._crossings = new_crossings

    def _is_merged_edge(self, edge: Edge):
        """
        returns True if the edge must be removed, False otherwise
        :param edge: the edge to consider
        :return: flag remove_edge
        """
        start_node_id = edge.getFromNode().getID()
        end_node_id = edge.getToNode().getID()

        return any(
            start_node_id in merged_nodes and end_node_id in merged_nodes
            for merged_nodes in self.merged_dictionary.values())

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

    def _calculate_centroid(self, nodes):
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

    def auto_generate_traffic_light_system(self,
                                           lanelet_id: int,
                                           cycle_time: int = 90) -> bool:
        """
        Automatically generate a TLS for the given intersection
        param: lanelet_id: id of lanelet in junction to generate Traffic Lights for
        param: cycle_time: total duration of a traffic light cycle in seconds
        :return: if the conversion was successful
        """
        if not self._output_file:
            logging.error("Need to call convert_to_net_file first")
            return False

        # did the user select an incoming lanelet to the junction?
        if not lanelet_id in self.lanelet_id2junction:
            lanelet: Lanelet = self.lanelet_network.find_lanelet_by_id(
                lanelet_id)
            if not lanelet:
                logging.warning("Invalid lanelet: {}".format(lanelet_id))
                return False
            # if the selected lanelet is not an incoming one, check the prececessors
            pred_ids = [
                pred for pred in lanelet.predecessor
                if pred in self.lanelet_id2junction
            ]
            if len(pred_ids) == 0:
                logging.info(
                    "No junction found for lanelet {}".format(lanelet_id))
                return False
            lanelet_id = pred_ids[0]

        # does the lanelet have predefined traffic light?
        # If so guess signals for them and copy the corresponding position
        guess_signals = False
        if self.lanelet_network.find_lanelet_by_id(lanelet_id).traffic_lights:
            guess_signals = True

        # auto generate the TLS with netconvert
        junction = self.lanelet_id2junction[lanelet_id]
        command = "netconvert --sumo-net-file=" + self._output_file + \
                  " --output-file=" + self._output_file + \
                  " --tls.guess=true" + \
                  " --tls.guess-signals=" + ('true' if guess_signals else 'false') + \
                  " --tls.group-signals=true" + \
                  " --tls.cycle.time=" + str(cycle_time) + \
                  " --tls.set=" + str(junction.id)
        try:
            out = subprocess.check_output(command.split(),
                                          timeout=5.,
                                          stderr=subprocess.STDOUT,
                                          shell=True)
            if "error" in str(out).lower():
                return False
        except Exception as e:
            logging.error(e)
            return False

        # add the generated tls to the lanelet_network
        self._read_junctions_from_net_file(self._output_file)
        # update the read junction
        junction = self.lanelet_id2junction[lanelet_id]

        with open(self._output_file, "r") as f:
            xml = ET.parse(f)

        # parse TLS from generated xml file
        def get_tls(xml, junction) -> TLSProgram:
            for tl_logic in xml.findall("tlLogic"):
                if not int(tl_logic.get("id")) == junction.id: continue

                tls_program = TLSProgram(tl_logic.get("programID"),
                                         int(tl_logic.get("offset")),
                                         tl_logic.get("type"))
                for phase in tl_logic.findall("phase"):
                    tls_program.addPhase(phase.get("state"),
                                         int(phase.get("duration")))
                return tls_program

        tls_program = get_tls(xml, junction)

        # compute unused id value for the traffic lights
        next_cr_id = max_lanelet_network_id(self.lanelet_network) + 1

        # add Traffic Lights to the corresponding lanelets
        # TODO: somewhat hacky replace with proper connection reading
        for c in xml.findall('connection'):
            tl = c.get("tl")
            if not (tl and int(tl) == junction.id): continue

            lanelet_id = self.lane_id2lanelet_id["{}_{}".format(
                c.get('from'), c.get("fromLane"))]
            lanelet = self.lanelet_network.find_lanelet_by_id(lanelet_id)
            link_index = int(c.get("linkIndex"))

            # sensible defaults for newly generated traffic light
            # TODO: This assuems right-hand traffic
            position = lanelet.right_vertices[-1]
            time_offset = tls_program.getOffset()
            direction = TrafficLightDirection.ALL
            active = True

            # replace current traffic light if one exists on the lanelet
            if lanelet.traffic_lights:
                traffic_lights: List[TrafficLight] = [
                    self.lanelet_network.find_traffic_light_by_id(id)
                    for id in lanelet.traffic_lights
                ]
                tl = traffic_lights[0]
                # copy attributes from old TrafficLight to new one
                position = tl.position
                direction = tl.direction
                active = tl.active
                # remove old traffic light from lanelet
                lanelet._traffic_lights -= set([tl.traffic_light_id])

            traffic_light = TrafficLight(next_cr_id, [
                TrafficLightCycleElement(
                    traffic_light_states_SUMO2CR[state[link_index]],
                    int(duration / self.conf.dt))
                for state, duration in tls_program.getPhases()
            ], position, time_offset, direction, active)
            next_cr_id += 1

            self.lanelet_network.add_traffic_light(traffic_light,
                                                   set([lanelet_id]))

        remove_unreferenced_traffic_lights(self.lanelet_network)
        return True

    def write_intermediate_files(self, output_path):
        """
        Function for writing the edges and nodes files in xml format
        :param output_path: the relative path of the output
        :return: None
        """
        self._write_edges_file(output_path)
        self._write_nodes_file(output_path)
        self._write_connections_file(output_path)
        self._write_traffic_file(output_path)

    def _write_edges_file(self, output_path):
        """
        Function for writing the edges file
        :param output_path: path for the file
        :return: nothing
        """
        with open(os.path.join(os.path.dirname(output_path), 'edges.net.xml'),
                  'w+') as output_file:
            sumolib.writeXMLHeader(output_file, '')
            root = ET.Element('root')
            edges = ET.SubElement(root, 'edges')
            for edge in self.new_edges.values():
                edges.append(ET.fromstring(edge.toXML()))

            # pretty print & write the generated xml
            output_file.write(
                minidom.parseString(ET.tostring(
                    edges, method="xml")).toprettyxml(indent="\t"))

    def _write_nodes_file(self, output_path):
        """
        Functio for writing the nodes file
        :param output_path: path for the file
        :return: nothing
        """
        with open(os.path.join(os.path.dirname(output_path), 'nodes.net.xml'),
                  'w+') as output_file:
            sumolib.writeXMLHeader(output_file, '')
            root = ET.Element('root')
            nodes = ET.SubElement(root, 'nodes')

            for node in self.new_nodes.values():
                nodes.append(ET.fromstring(node.toXML()))

            # pretty print & write the generated xml
            output_file.write(
                minidom.parseString(ET.tostring(
                    nodes, method="xml")).toprettyxml(indent="\t"))

    def _write_connections_file(self, output_path):
        """
        Function for writing the connections file
        :param output_path: path for the file
        :return: nothing
        """
        with open(
            os.path.join(os.path.dirname(output_path),
                         '_connections.net.xml'), 'w+') as output_file:
            sumolib.writeXMLHeader(output_file, '')
            root = ET.Element('root')
            connections = ET.SubElement(root, 'connections')
            for connection in self._new_connections:
                connections.append(ET.fromstring(connection.toXML()))
            for crossings in self._crossings.values():
                for crossing in crossings:
                    connections.append(ET.fromstring(crossing.toXML()))

            # pretty print & write the generated xml
            output_file.write(
                minidom.parseString(ET.tostring(
                    connections, method="xml")).toprettyxml(indent="\t"))

    def _write_traffic_file(self, output_path):
        """
        Writes the tll.net.xml file to disk
        :param output_path: path for the file
        """
        with open(os.path.join(os.path.dirname(output_path), "_tll.net.xml"),
                  "w+") as f:
            sumolib.writeXMLHeader(f, '')
            tlLogics = ET.Element('tlLogics')

            for tls in self.traffic_light_signals.values():
                tls_xml = ET.fromstring(tls.toXML())
                tlLogics.append(tls_xml.find('tlLogic'))
                for conn in tls_xml.findall('connection'):
                    tlLogics.append(conn)
            f.write(
                minidom.parseString(ET.tostring(
                    tlLogics, method="xml")).toprettyxml(indent="\t"))

    def merge_intermediate_files(self, output_path: str, cleanup=True) -> bool:
        """
        Function that merges the edges and nodes files into one using netconvert
        :param output_path: the relative path of the output
        :param cleanup: deletes temporary input files after creating net file (only deactivate for debugging)
        :return: bool: returns False if conversion fails
        """

        files = {
            "nodes": "nodes.net.xml",
            "edges": "edges.net.xml",
            "connections": "_connections.net.xml",
            "tll": "_tll.net.xml"
        }

        def join(output_path, file_name):
            return os.path.join(os.path.dirname(output_path), file_name)

        # The header of the xml files must be removed
        to_remove = ["options", "xml"]
        for file_name in files.values():
            # Removing header in file
            path = join(output_path, file_name)
            with open(path, 'r') as file:
                lines = file.readlines()
            with open(path, 'w') as file:
                for line in lines:
                    if not any(word in line for word in to_remove):
                        file.write(line)

        self._nodes_file = join(output_path, files["nodes"])
        self._edges_file = join(output_path, files["edges"])
        self._connections_file = join(output_path, files["connections"])
        self._tll_file = join(output_path, files["tll"])
        self._output_file = str(output_path)
        # Calling of Netconvert
        bashCommand = "netconvert --plain.extend-edge-shape=true" \
                      " --no-turnarounds=true" \
                      " --junctions.internal-link-detail=20" \
                      " --geometry.avoid-overlap=true" \
                      " --offset.disable-normalization=true" \
                      " --node-files=" + self._nodes_file + \
                      " --edge-files=" + self._edges_file + \
                      " --connection-files=" + self._connections_file + \
                      " --tllogic-files=" + self._tll_file + \
                      " --output-file=" + self._output_file + \
                      " --geometry.remove.keep-edges.explicit=true" + \
                      " --seed " + str(SumoConfig.random_seed)
        # "--junctions.limit-turn-speed=6.5 " \
        # "--geometry.max-segment-length=15 " \
        success = True
        try:
            _ = subprocess.check_output(bashCommand.split(), timeout=5.0)
            self._read_junctions_from_net_file(self._output_file)

        except FileNotFoundError as e:
            if 'netconvert' in e.filename:
                warnings.warn("Is netconvert installed and added to PATH?")
            success = False
        except Exception as e:
            logging.error(e)
            success = False

        if cleanup and success:
            for file in files.values():
                os.remove(join(output_path, file))
        return success

    def _read_junctions_from_net_file(self, filename: str):
        # parse junctions from .net.xml
        with open(filename, 'r') as f:
            root = ET.parse(f)

        for junction_xml in root.findall("junction"):
            inc_lanes: List[Lane] = [
                self.lanes[lane_id]
                for lane_id in junction_xml.get('incLanes').split()
                # we don't care about internal junction added by netconvert
                if lane_id in self.lanes
            ]
            shape = [
                tuple([float(i) for i in s.split(",")])
                for s in junction_xml.get('shape').split()
            ]
            junction = Junction(id=int(junction_xml.get('id')),
                                j_type=junction_xml.get('type'),
                                x=float(junction_xml.get('x')),
                                y=float(junction_xml.get('y')),
                                incLanes=inc_lanes,
                                shape=shape)
            for lanelet_id in [
                self.lane_id2lanelet_id[l.getID()] for l in inc_lanes
            ]:
                self.lanelet_id2junction[lanelet_id] = junction

    @staticmethod
    def rewrite_netfile(output: str):
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
                if key == 'type' and (value == 'priority'
                                      or value == 'unregulated'):
                    junction.set(key, 'zipper')

        tree.write(output, encoding='utf-8', xml_declaration=True)

    def debug_lanelet_net(self,
                          with_lane_id=True,
                          with_succ_pred=False,
                          with_adj=False,
                          with_speed=False,
                          figure_title=None):
        """
        Debug function for showing input CommonRoad map to be converted
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
                centroid = np.array(
                    l.convert_to_polygon().shapely_object.centroid)
                plt.text(centroid[0],
                         centroid[1],
                         id,
                         zorder=100,
                         size=8,
                         color='r',
                         verticalalignment='top')
            if with_succ_pred:
                info = info + '\nsucc: ' + str(l.successor) + ' pred: ' + str(
                    l.predecessor)
            if with_adj:
                info = info + ' \nadj_l: ' + str(
                    l.adj_left) + '; adj_l_same_dir: ' + str(
                    l.adj_left_same_direction)
                info = info + ' \nadj_r: ' + str(
                    l.adj_right) + '; adj_r_same_dir: ' + str(
                    l.adj_right_same_direction)
            if with_speed:
                info = info + '\nspeed limit: ' + str(l.speed_limit)
            plt.plot(l.center_vertices[0, 0], l.center_vertices[0, 1], 'x')
            plt.text(l.center_vertices[0, 0] + noise,
                     l.center_vertices[0, 1] + noise,
                     info,
                     zorder=100,
                     size=8,
                     verticalalignment='top')
        plt.show()

    def convert_to_net_file(self, output_folder: str) -> bool:
        """
        Convert the Commonroad scenario to a net.xml file, specified by the absolute  path output_file.
        :param path of the returned net.xml file
        :return returns whether conversion was successful
        """

        output_path = os.path.join(output_folder,
                                   self.conf.scenario_name + '.net.xml')
        logging.info("Converting to SUMO Map")
        self._convert_map()

        logging.info("Merging Intermediate Files")
        self.write_intermediate_files(output_path)
        conversion_possible = self.merge_intermediate_files(output_path,
                                                            cleanup=False)
        if not conversion_possible:
            logging.error("Error converting map, see above for details")
            return False

        logging.info("Generating Traffic Routes")
        return self._generate_routes(output_path)

    def _generate_routes(self, net_file: str) -> bool:
        """
        Automatically generates traffic routes from the given .net.xml file

        :param net_file: Path of the SUMO .net.xml file
        :return bool: If the conversion was successful
        """
        if len(self.conf.ego_ids) > self.conf.n_ego_vehicles:
            logging.error("total number of given ego_vehicles must be <= n_ego_vehicles, but {}not<={}" \
                          .format(len(self.conf.ego_ids), self.conf.n_ego_vehicles))
            return False

        if self.conf.n_ego_vehicles > self.conf.n_vehicles_max:
            logging.error(
                "Number of ego vehicles needs to be <= than the total number of vehicles. n_ego_vehicles: {} > n_vehicles_max: {}"
                    .format(self.conf.n_ego_vehicles, self.conf.n_vehicles_max))
            return False

        scenario_name = get_scenario_name_from_netfile(net_file)
        out_folder = os.path.dirname(net_file)

        add_file = self._generate_add_file(scenario_name, out_folder)
        rou_files = self._generate_rou_file(net_file, scenario_name,
                                            out_folder)
        self.sumo_cfg_file = self._generate_cfg_file(scenario_name, net_file,
                                                     rou_files, add_file,
                                                     out_folder)
        return True

    def _generate_add_file(self, scenario_name: str,
                           output_folder: str) -> str:
        """
        Generate additional file for sumo scenario to define attributes of different vehicle types.

        :param output_folder: the generated add file will be saved here
        :return: additional file
        """
        add_file = os.path.join(output_folder, scenario_name + '.add.xml')

        # create file
        domTree = minidom.Document()
        additional_node = domTree.createElement("additional")
        domTree.appendChild(additional_node)
        vType_dist_node = domTree.createElement("vTypeDistribution")
        vType_dist_node.setAttribute("id", "DEFAULT_VEHTYPE")
        additional_node.appendChild(vType_dist_node)

        # config parameters for easy access
        veh_distribution = self.conf.veh_distribution
        veh_params = self.conf.veh_params
        driving_params = self.conf.driving_params

        for veh_type, probability in veh_distribution.items():
            if probability > 0:
                vType_node = domTree.createElement("vType")
                vType_node.setAttribute("id", veh_type)
                vType_node.setAttribute("guiShape", veh_type)
                vType_node.setAttribute("vClass", veh_type)
                vType_node.setAttribute("probability", str(probability))
                for att_name, setting in veh_params.items():
                    att_value = setting[veh_type]
                    if type(att_value) is Interval:
                        att_value = np.random.uniform(att_value.start,
                                                      att_value.end, 1)[0]
                        att_value = str("{0:.2f}".format(att_value))
                    else:
                        att_value = str(att_value)
                    vType_node.setAttribute(att_name, att_value)
                for att_name, value_interval in driving_params.items():
                    att_value = np.random.uniform(value_interval.start,
                                                  value_interval.end, 1)[0]
                    vType_node.setAttribute(att_name,
                                            str("{0:.2f}".format(att_value)))
                vType_dist_node.appendChild(vType_node)
            #     print("The probability of the vehicle type %s is %s." % (veh_type, probability))
            # else:
            #     print("The probability of the vehicle type %s is 0." % veh_type)

        with open(add_file, "w") as f:
            domTree.documentElement.writexml(f, addindent="\t", newl="\n")

        logging.info("Additional file written to {}".format(add_file))
        return add_file

    def _generate_rou_file(
        self,
        net_file: str,
        scenario_name: str,
        out_folder: str = None,
    ) -> str:
        """
        Creates route & trips files using randomTrips generator.

        :param net_file: path of .net.xml file
        :param scenario_name: name of the CR Scenario
        :param out_folder: output folder of route file (same as net_file if None)
        :return: path of route file
        """

        total_lane_length = get_total_lane_length_from_netfile(net_file)
        if total_lane_length is not None:
            # calculate period based on traffic frequency depending on map size
            period = 1 / (self.conf.max_veh_per_km *
                          (total_lane_length / 1000) * self.conf.dt)
            logging.info(
                'SUMO traffic generation: traffic frequency is defined based on the total lane length of the road network.'
            )
        elif self.conf.veh_per_second is not None:
            # vehicles per second
            period = 1 / (self.conf.veh_per_second * self.conf.dt)
            logging.info(
                'SUMO traffic generation: the total_lane_length of the road network is not available. '
                'Traffic frequency is defined based on equidistant depature time.'
            )
        else:
            period = 0.5
            logging.info(
                'SUMO traffic generation: neither total_lane_length nor veh_per_second is defined. '
                'For each second there are two vehicles generated.')
        # step_per_departure = ((conf.departure_interval_vehicles.end - conf.departure_interval_vehicles.start) / n_vehicles_max)

        # filenames
        route_files: Dict[str, str] = {
            'vehicle':
                os.path.join(out_folder, scenario_name + ".vehicles.rou.xml"),
            "pedestrian":
                os.path.join(out_folder, scenario_name + ".pedestrians.rou.xml")
        }
        trip_files: Dict[str, str] = {
            'vehicle':
                os.path.join(out_folder, scenario_name + '.vehicles.trips.xml'),
            'pedestrian':
                os.path.join(out_folder, scenario_name + '.pedestrian.trips.xml')
        }
        add_file = os.path.join(out_folder, scenario_name + '.add.xml')

        def run(cmd) -> bool:
            try:
                subprocess.check_output(cmd)
                return True
            except subprocess.CalledProcessError as e:
                return False
                # raise RuntimeError(
                #     "Command '{}' return with error (code {}): {}".format(
                #         e.cmd, e.returncode, e.output)) from e

        # create vehicle route file
        run([
            'python',
            os.path.join(os.environ['SUMO_HOME'], 'tools',
                         'randomTrips.py'), '-n', net_file, '-o',
            trip_files['vehicle'], '-r', route_files["vehicle"], '-b',
            str(self.conf.departure_interval_vehicles.start), '-e',
            str(self.conf.departure_interval_vehicles.end), '-p',
            str(period), '--allow-fringe', '--fringe-factor',
            str(self.conf.fringe_factor), "--seed",
            str(self.conf.random_seed),
            '--trip-attributes=departLane=\"best\" departSpeed=\"max\" departPos=\"base\"'
        ])
        # create pedestrian routes
        run([
            'python',
            os.path.join(os.environ['SUMO_HOME'], 'tools',
                         'randomTrips.py'), '-n', net_file, '-o',
            trip_files['pedestrian'], '-r', route_files["pedestrian"], '-b',
            str(self.conf.departure_interval_vehicles.start), '-e',
            str(self.conf.departure_interval_vehicles.end), "-p",
            str(1 - self.conf.veh_distribution['pedestrian']),
            '--allow-fringe', '--fringe-factor',
            str(self.conf.fringe_factor), "--persontrips", "--seed",
            str(self.conf.random_seed),
            '--trip-attributes= modes=\"public car\" departPos=\"base\"'
        ])

        if self.conf.n_ego_vehicles != 0:
            # get ego ids and add EGO_ID_START prefix
            ego_ids = self._find_ego_ids_by_departure_time(
                route_files["vehicle"])
            write_ego_ids_to_rou_file(route_files["vehicle"], ego_ids)

        return route_files

    def _find_ego_ids_by_departure_time(self, rou_file: str) -> list:
        """
        Returns ids of vehicles from route file which match desired departure time as close as possible.

        :param rou_file: path of route file
        :param n_ego_vehicles:  number of ego vehicles
        :param departure_time_ego: desired departure time ego vehicle
        :param ego_ids: if desired ids of ego_vehicle known, specify here

        """
        vehicles = sumolib.output.parse_fast(rou_file, 'vehicle',
                                             ['id', 'depart'])
        dep_times = []
        veh_ids = []
        for veh in vehicles:
            veh_ids.append(veh[0])
            dep_times.append(int(float(veh[1])))

        if n_ego_vehicles > len(veh_ids):
            warnings.warn(
                'only {} vehicles in route file instead of {}'.format(
                    len(veh_ids), n_ego_vehicles),
                stacklevel=1)
            n_ego_vehicles = len(veh_ids)

        # check if specified ids exist
        for i in self.conf.ego_ids:
            if i not in veh_ids:
                warnings.warn(
                    '<generate_rou_file> id {} not in route file!'.format_map(
                        i))
                del i

        # assign vehicles as ego by finding closest departure time
        dep_times = np.array(dep_times)
        veh_ids = np.array(veh_ids)
        greater_start_time = np.where(
            dep_times >= self.conf.departure_time_ego)[0]
        for index in greater_start_time:
            if len(self.conf.ego_ids) == n_ego_vehicles:
                break
            else:
                self.conf.ego_ids.append(veh_ids[index])

        if len(self.conf.ego_ids) < n_ego_vehicles:
            n_ids_missing = n_ego_vehicles - len(self.conf.ego_ids)
            self.conf.ego_ids.extend(
                (veh_ids[greater_start_time[0] -
                         n_ids_missing:greater_start_time[0]]).tolist())

        return self.conf.ego_ids

    def _generate_cfg_file(self, scenario_name: str, net_file: str,
                           route_files: Dict[str, str], add_file: str,
                           output_folder: str) -> str:
        """
        Generates the configuration file according to the scenario name to the specified output folder.

        :param scenario_name: name of the scenario used for the cfg file generation.
        :param net_file: path of the generated sumo .net.xml file
        :param rou_file: path of the generated sumo .rou.xml file
        :param rou_file: path of the generated sumo .add.xml file
        :param output_folder: the generated cfg file will be saved here

        :return: the path of the generated cfg file.
        """

        sumo_cfg_file = os.path.join(output_folder,
                                     scenario_name + '.sumo.cfg')
        tree = ET.parse(
            os.path.join(os.path.dirname(__file__), DEFAULT_CFG_FILE))

        updated_fields = {
            '*/net-file':
                os.path.basename(net_file),
            '*/route-files':
                ",".join([os.path.basename(f) for f in route_files.values()]),
            '*/additional-files':
                os.path.basename(add_file),
        }
        for k, v in updated_fields.items():
            tree.findall(k)[0].attrib['value'] = v

        for elem in tree.iter():
            if (elem.text):
                elem.text = elem.text.strip()
            if (elem.tail):
                elem.tail = elem.tail.strip()
        rough_string = ET.tostring(tree.getroot(), encoding='utf-8')
        reparsed = minidom.parseString(rough_string)

        with open(sumo_cfg_file, "w") as f:
            f.write(reparsed.toprettyxml(indent="\t", newl="\n"))

        return sumo_cfg_file
