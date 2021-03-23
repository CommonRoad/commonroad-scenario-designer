""" This class contains functions for converting a CommonRoad map into a .net.xml SUMO map
"""
import itertools
import logging
import os
import subprocess
import sys
import warnings
from collections import defaultdict
from copy import deepcopy
from functools import reduce
from itertools import groupby
from typing import Dict, List, Set, Tuple, Iterable
# TODO: Move to a single XML lib
from xml.dom import minidom
from xml.etree import cElementTree as ET

import lxml.etree as etree
import matplotlib.colors as mcolors
import networkx as nx
import numpy as np
import sumolib
from matplotlib import pyplot as plt

try:
    import pycrccosy
    from commonroad_ccosy.geometry.util import resample_polyline, compute_curvature_from_polyline, \
        chaikins_corner_cutting
except ImportError:
    warnings.warn(
        f"Unable to import pycrccosy, converting static scenario into interactive is not supported!")

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.util import Interval
from commonroad.prediction.prediction import TrajectoryPrediction
from commonroad.scenario.trajectory import State
from commonroad.scenario.lanelet import LaneletNetwork, Lanelet
from commonroad.scenario.obstacle import ObstacleRole, ObstacleType
from commonroad.scenario.scenario import Scenario
from commonroad.scenario.traffic_sign import SupportedTrafficSignCountry, TrafficLight, \
    TrafficLightCycleElement, TrafficLightDirection, TrafficSign
from commonroad.scenario.traffic_sign_interpreter import TrafficSigInterpreter

from sumocr.maps.scenario_wrapper import AbstractScenarioWrapper

from crmapconverter.sumo_map.sumolib_net import (TLS, Connection, Crossing, Edge, Junction, Lane,
                                                 Node, TLSProgram, Phase, SignalState, NodeType, RightOfWay,
                                                 VehicleType)
from crmapconverter.sumo_map.errors import ScenarioException
from crmapconverter.sumo_map.util import (_find_intersecting_edges,
                                          get_total_lane_length_from_netfile, max_lanelet_network_id,
                                          merge_lanelets, min_cluster,
                                          remove_unreferenced_traffic_lights,
                                          write_ego_ids_to_rou_file, update_edge_lengths)

from crmapconverter.sumo_map.config import SumoConfig
from .mapping import (get_sumo_edge_type, traffic_light_states_SUMO2CR, VEHICLE_TYPE_CR2SUMO, VEHICLE_NODE_TYPE_CR2SUMO,
                      DEFAULT_CFG_FILE,
                      get_edge_types_from_template)
from .traffic_sign import TrafficSignEncoder
from .traffic_light import TrafficLightEncoder


# This file is used as a template for the generated .sumo.cfg files

class CR2SumoMapConverter(AbstractScenarioWrapper):
    """Converts CommonRoad map to sumo map .net.xml"""

    def __init__(self,
                 lanelet_network: LaneletNetwork,
                 conf: SumoConfig):
        """
        :param lanelet_network: lanelet network to be converted
        :param conf: configuration file for additional map conversion parameters
        """
        self.lanelet_network: LaneletNetwork = lanelet_network
        self.conf: SumoConfig = conf
        self.country_id = SupportedTrafficSignCountry(conf.country_id) if isinstance(conf.country_id,
                                                                                     str) else conf.country_id
        # all the nodes of the map, key is the node ID
        self.nodes: Dict[int, Node] = {}
        # all the edges of the map, key is the edge ID
        self.edges: Dict[int, Edge] = {}
        # dictionary for the shape of the edges
        self._points_dict: Dict[int, np.ndarray] = {}
        # all the connections of the map
        # lane_id -> list(lane_id)
        self._connections: Dict[str, List[str]] = defaultdict(list)
        self._new_connections: Set[Connection] = set()
        # dict of merged_node_id and Crossing
        self._crossings: Dict[int, Set[Lanelet]] = dict()
        # key is the ID of the edges and value the ID of the lanelets that compose it
        self.lanes_dict: Dict[int, List[int]] = {}
        self.lanes: Dict[str, Lane] = {}
        # edge_id -> length (float)
        self.edge_lengths = {}
        # list of the already explored lanelets
        self._explored_lanelets = []
        self._max_vehicle_width = max(self.conf.veh_params['width'].values())

        # traffic signs
        self._traffic_sign_interpreter: TrafficSigInterpreter = TrafficSigInterpreter(
            self.country_id, self.lanelet_network)
        # Read Edge Types from template
        self.edge_types = get_edge_types_from_template(self.country_id)

        self.lane_id2lanelet_id: Dict[str, int] = {}
        self.lanelet_id2lane_id: Dict[int, str] = {}
        self.lanelet_id2edge_id: Dict[int, int] = {}
        self.lanelet_id2edge_lane_id: Dict[int, int] = {}
        # generated junctions by NETCONVERT
        self.lanelet_id2junction: Dict[int, Junction] = {}

        # for an edge_id gives id's of start and end nodes
        self._start_nodes: Dict[int, int] = {}
        self._end_nodes: Dict[int, int] = {}

        self.traffic_light_signals = TLS()

        # NETCONVERT files
        self._nodes_file = ""
        self._edges_file = ""
        self._connections_file = ""
        self._traffic_file = ""
        # path to SUMO typ.xml file
        self._type_file = ""
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
        self._encode_traffic_signs()
        self._create_traffic_lights()

    def _find_lanes(self):
        """
        Convert a CommonRoad net into a SUMO net
        sumo_net contains the converted net
        """

        self._points_dict = {
            lanelet.lanelet_id: lanelet.center_vertices
            for lanelet in self.lanelet_network.lanelets
        }
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
                current_lanelet = self.lanelet_network.find_lanelet_by_id(
                    ordered_lanelet_ids[-1])

            self.lanes_dict[rightmost_lanelet.lanelet_id] = ordered_lanelet_ids
            self.edge_lengths[rightmost_lanelet.lanelet_id] = min([lanelet.distance[-1] for lanelet in lanelets])

            for i_lane, l_id in enumerate(ordered_lanelet_ids):
                self.lanelet_id2edge_id[l_id] = rightmost_lanelet.lanelet_id
                self.lanelet_id2edge_lane_id[l_id] = i_lane

    def _compute_node_coords(self, lanelets, index: int):
        vertices = np.array([l.center_vertices[index] for l in lanelets])
        return np.mean(vertices, axis=0)

    def _init_nodes(self):
        # creation of the start and end nodes
        # start node
        self.node_id_next = 1
        self._start_nodes = {}  # contains start nodes of each edge{edge_id: node_id}
        self._end_nodes = {}  # contains end nodes of each edge{edge_id: node_id}

        for edge_id, lanelet_ids in self.lanes_dict.items():
            self._create_node(edge_id, lanelet_ids, 'from')
            self._create_node(edge_id, lanelet_ids, 'to')

    def _create_node(self, edge_id: int, lanelet_ids: List[int], node_type: str):
        """
        Creates new node for an edge or assigns it to an existing node.
        :param edge_id: edge ID
        :param lanelet_ids: list of lanelet ids
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
                    try:
                        [conn_edges.add(self.lanelet_id2edge_id[succ]) for succ in conn_lanelet]
                    except KeyError as exp:
                        raise ScenarioException(
                            f"The lanelet network is inconsistent in scenario {self.scenario_name}, "
                            f"there is a problem with adjacency of the lanelet {exp}")

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
                                                     NodeType.PRIORITY,
                                                     coords,
                                                     right_of_way=RightOfWay.EDGE_PRIORITY)
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
            self.nodes[self.node_id_next] = Node(self.node_id_next,
                                                 NodeType.PRIORITY,
                                                 coords,
                                                 right_of_way=RightOfWay.EDGE_PRIORITY)
            if node_type == "from":
                self._start_nodes[edge_id] = self.node_id_next
            else:
                self._end_nodes[edge_id] = self.node_id_next

            self.node_id_next += 1

    def _create_sumo_edges_and_lanes(self):
        """
        Creates edges for net file with previously collected edges and nodes.
        :return:
        """

        def calculate_lanelet_width_from_cr(lanelet: Lanelet) -> float:
            """
            Calculate the average width of a lanelet.
            :param lanelet: the lane whose width is to be calculated
            :return: average_width
            """
            helper_matrix = lanelet.right_vertices - lanelet.left_vertices
            distance_array = helper_matrix[:, 0] ** 2 + helper_matrix[:, 1] ** 2
            average_width = np.sqrt(np.min(distance_array))
            return average_width

        for edge_id, lanelet_ids in self.lanes_dict.items():
            # Creation of Edge, using id as name
            start_node = self.nodes[self._start_nodes[edge_id]]
            end_node = self.nodes[self._end_nodes[edge_id]]

            lanelet_types = [lanelet_type for lanelet_id in lanelet_ids for lanelet_type in
                             self.lanelet_network.find_lanelet_by_id(lanelet_id).lanelet_type]
            edge_type = get_sumo_edge_type(self.edge_types, self.country_id, *lanelet_types)

            edge = Edge(id=edge_id,
                        from_node=start_node,
                        to_node=end_node,
                        type_id=edge_type.id,
                        name=f"edge_{edge_id}")

            self.edges[edge_id] = edge
            if self.conf.overwrite_speed_limit:
                speed_limit = self.conf.overwrite_speed_limit
            else:
                speed_limit = self._traffic_sign_interpreter.speed_limit(
                    frozenset([lanelet.lanelet_id]))
                if speed_limit is None or np.isinf(speed_limit):
                    speed_limit = self.conf.unrestricted_speed_limit_default

            for lanelet_id in lanelet_ids:
                shape = self._points_dict[lanelet_id]
                lanelet = self.lanelet_network.find_lanelet_by_id(lanelet_id)
                lanelet_width = calculate_lanelet_width_from_cr(lanelet)

                lane = Lane(edge,
                            speed=speed_limit,
                            length=self.edge_lengths[edge_id],
                            width=lanelet_width,
                            shape=shape)
                self.lanes[lane.id] = lane
                self.lane_id2lanelet_id[lane.id] = lanelet_id
                self.lanelet_id2lane_id[lanelet_id] = lane.id

        # set oncoming lanes
        for edge_id, lanelet_ids in self.lanes_dict.items():
            leftmost_lanelet = self.lanelet_network.find_lanelet_by_id(
                lanelet_ids[-1])
            if leftmost_lanelet.adj_left is not None:
                self.lanes[self.lanelet_id2lane_id[lanelet_ids[-1]]] \
                    .setAdjacentOpposite(self.lanelet_id2lane_id[leftmost_lanelet.adj_left])

        for edge in self.edges.values():
            for e in edge.to_node.outgoing:
                edge.add_outgoing(e)
            for e in edge.from_node.incoming:
                edge.add_incoming(e)

    def _init_connections(self):
        """
        Init connections, doesn't consider junctions yet.
        :return:
        """
        for l in self.lanelet_network.lanelets:
            if l.successor:
                self._connections[self.lanelet_id2lane_id[l.lanelet_id]] += [self.lanelet_id2lane_id[succ]
                                                                             for succ in l.successor]

    def _filter_disallowed_vehicle_classes(self, max_curvature: float,
                                           lanelet_width, lanelet_id) -> List[str]:
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
                if veh_length ** 2 > max_vehicle_length_sq and veh_length > self.conf.veh_params['length']['passenger']:
                    disallow.append(veh_class)
                    # print("{} disallowed on lanelet {}, allowed max_vehicle_length={}".format(veh_class, lanelet_id,
                    #                                                                           max_vehicle_length))
        return disallow

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

    def _encode_traffic_signs(self):
        """
        Encodes all traffic signs and writes the according changes to relevant nodes / edges
        :return:
        """
        encoder = TrafficSignEncoder(self.edge_types)
        traffic_signs: Dict[int, TrafficSign] = {t.traffic_sign_id: t
                                                 for t in self.lanelet_network.traffic_signs}
        for lanelet in self.lanelet_network.lanelets:
            if not lanelet.traffic_signs:
                continue
            edge_id = self.lanelet_id2edge_id[lanelet.lanelet_id]
            if edge_id not in self.new_edges:
                logging.warning(f"Merged Edge {edge_id} with traffic signs {lanelet.traffic_signs}. "
                                f"These Traffic signs will not be converted.")
                continue
            edge = self.new_edges[edge_id]
            for traffic_sign_id in lanelet.traffic_signs:
                traffic_sign = traffic_signs[traffic_sign_id]
                encoder.apply(traffic_sign, edge)
        encoder.encode()

    def _merge_junctions_intersecting_lanelets(self):
        """
        Merge nodes when their connecting edges intersect.
        :return:
        """
        # new dictionary for the merged nodes
        self.new_nodes: Dict[int, Node] = self.nodes.copy()
        # new dictionary for the edges after the simplifications
        self.new_edges: Dict[int, Edge] = {}
        # key is the merged node, value is a list of the nodes that form the merged node
        self.merged_dictionary: Dict[int, Set[Node]] = {}
        self.replaced_nodes: Dict[int, List[int]] = defaultdict(list)

        clusters: Dict[int, Set[Node]] = defaultdict(set)
        next_cluster_id = 0
        # crossings are additional info for a cluster
        clusters_crossing: Dict[int, Set[Lanelet]] = defaultdict(set)

        # INTERSECTION BASED CLUSTERING
        for intersection in self.lanelet_network.intersections:
            intersecting_lanelets = {
                lanelet_id
                for incoming in intersection.incomings
                for lanelet_id in incoming.successors_right | incoming.successors_left | incoming.successors_straight
            }
            intersecting_edges: Set[Edge] = {self.edges[self.lanelet_id2edge_id[step]]
                                             for step in intersecting_lanelets | intersection.crossings}
            clusters[next_cluster_id] = {node for e in intersecting_edges for node in [e.from_node, e.to_node]}

            # generate partial Crossings
            clusters_crossing[next_cluster_id] = {
                self.lanelet_network.find_lanelet_by_id(lanelet_id) for lanelet_id in intersection.crossings
            }
            next_cluster_id += 1

        # merge overlapping clusters
        while True:
            try:
                a_id, b_id = next((a_id, b_id)
                                  for a_id, a in clusters.items()
                                  for b_id, b in clusters.items()
                                  if a_id < b_id and a & b)
                clusters[a_id] |= clusters[b_id]
                del clusters[b_id]
                clusters_crossing[a_id] |= clusters_crossing[b_id]
                del clusters_crossing[b_id]
            except StopIteration:
                break

        # Expand merged clusters by all lanelets intersecting each other.
        # merging based on Lanelets intersecting
        intersecting_edges: Dict[int, Set[int]] = defaultdict(set)
        for pair in _find_intersecting_edges(self.lanes_dict, self.lanelet_network):
            intersecting_edges[pair[0]].add(pair[1])
            intersecting_edges[pair[1]].add(pair[0])

        explored_nodes = set()
        for current_node in self.nodes.values():
            clusters_flat = {n for cluster in clusters.values() for n in cluster}
            if current_node in explored_nodes | clusters_flat:
                continue
            queue = [current_node]
            try:
                current_cluster_id = next(cluster_id
                                          for cluster_id, cluster in clusters.items()
                                          if current_node in cluster)
            except StopIteration:
                current_cluster_id = next_cluster_id
                next_cluster_id += 1

            current_cluster = clusters[current_cluster_id]
            # delete current_cluster from dict
            if current_cluster:
                clusters[current_cluster_id] = set()
                queue = list(current_cluster)

            while queue:
                expanded_node = queue.pop()
                if expanded_node in explored_nodes:
                    continue
                explored_nodes.add(expanded_node)

                incomings = {e.id for e in expanded_node.incoming}
                outgoings = {e.id for e in expanded_node.outgoing}
                neighbor_nodes = {node
                                  for edge_id in incomings | outgoings
                                  for intersecting in intersecting_edges[edge_id]
                                  for node in [self.edges[intersecting].from_node, self.edges[intersecting].to_node]}
                neighbor_nodes -= clusters_flat
                queue += list(neighbor_nodes)
                current_cluster |= neighbor_nodes

            clusters[current_cluster_id] = current_cluster

        # filter clusters with 0 nodes
        clusters = {cluster_id: cluster for cluster_id, cluster in clusters.items() if len(cluster) > 1}

        # MERGE COMPUTED CLUSTERS
        for cluster_id, cluster in clusters.items():
            logging.info(f"Merging nodes: {[n.id for n in cluster]}")

            # create new merged node
            def merge_cluster(cluster: Set[Node]) -> Node:
                cluster_ids = {n.id for n in cluster}
                merged_node = Node(id=self.node_id_next,
                                   node_type=NodeType.PRIORITY,
                                   coord=np.mean([node.coord for node in cluster], axis=0))
                self.node_id_next += 1
                self.new_nodes[merged_node.id] = merged_node
                for old_node_id in cluster_ids:
                    assert old_node_id not in self.replaced_nodes
                    self.replaced_nodes[old_node_id].append(merged_node.id)
                self.merged_dictionary[merged_node.id] = cluster_ids
                return merged_node

            # clustered nodes at the border of a network need to be merged
            # separately, so junctions at network boundaries are converted correctly
            no_outgoing = {node for node in cluster if not node.outgoing}
            no_incoming = {node for node in cluster if not node.incoming}
            inner_cluster = cluster - no_outgoing - no_incoming
            if inner_cluster:
                merged_node = merge_cluster(inner_cluster)
                # Make crossing lanelets globally available
                if cluster_id in clusters_crossing:
                    self._crossings[merged_node.id] = clusters_crossing[cluster_id]
            if no_outgoing:
                merge_cluster(no_outgoing)
            if no_incoming:
                merge_cluster(no_incoming)

        replace_nodes_old = deepcopy(self.replaced_nodes)
        explored_nodes_all = set()
        for old_node, new_nodes in replace_nodes_old.items():
            if old_node in explored_nodes_all:
                continue

            if len(new_nodes) > 1:
                new_candidates = deepcopy(new_nodes)
                new_node = new_nodes[0]
                to_merge = set()
                explored_candidates = set()

                while new_candidates:
                    # merge with merged junction
                    new_node_tmp = new_candidates.pop()
                    if new_node_tmp in explored_candidates:
                        continue
                    explored_candidates.add(new_node_tmp)
                    to_merge |= self.merged_dictionary[new_node_tmp]
                    for merged_node in self.merged_dictionary[new_node_tmp]:
                        if len(self.replaced_nodes[merged_node]) > 1:
                            new_candidates = list(
                                set(new_candidates + self.replaced_nodes[merged_node]) - explored_candidates
                            )

                for node_id in explored_candidates:
                    del self.merged_dictionary[node_id]
                    if node_id != new_node:
                        del self.new_nodes[node_id]

                self.merged_dictionary[new_node] = to_merge
                explored_nodes_all |= to_merge
                for merged_node in to_merge:
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

            edge_id = edge.id
            start_id = edge.from_node.id
            end_id = edge.to_node.id

            # update merged edges to from/to the merged node
            for new_node_id, merged_nodes in self.merged_dictionary.items():
                if start_id in merged_nodes:
                    edge.from_node = self.new_nodes[new_node_id]
                    break

            for new_node_id, merged_nodes in self.merged_dictionary.items():
                if end_id in merged_nodes:
                    edge.to_node = self.new_nodes[new_node_id]
                    break

            self.new_edges[edge_id] = edge

    def _create_lane_based_connections(self):
        """
        Instantiate a new dictionary with only the connections that are meaningful after the simplification of the net
        :return: nothing
        """
        edge_ids = [edge.id for edge in self.new_edges.values()]
        for from_lane, connections in self._connections.copy().items():
            if int(from_lane.split("_")[0]) not in edge_ids:
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
                if int(succ_lane.split("_")[0]) not in edge_ids:
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
                    via = path[0:-1]
                else:
                    shape = None
                    via = None
                connection = Connection(
                    from_edge=self.new_edges[int(from_lane.split("_")[0])],
                    to_edge=self.new_edges[int(path[-1].split("_")[0])],
                    from_lane=self.lanes[from_lane],
                    to_lane=self.lanes[path[-1]],
                    via_lane_id=via,
                    shape=shape,
                    keep_clear=True,
                    cont_pos=self.conf.wait_pos_internal_junctions)
                self._new_connections.add(connection)

    def _create_crossings(self):
        new_crossings = dict()
        for merged_node_id, crossing_lanelets in self._crossings.items():
            if not crossing_lanelets:
                continue
            merged_node = self.new_nodes[merged_node_id]
            adjacent_edges = {edge
                              for edge in self.new_edges.values()
                              if edge.from_node == merged_node
                              or edge.to_node == merged_node
                              }
            pedestrian_edges = {edge for edge in adjacent_edges
                                if VehicleType.PEDESTRIAN in self.edge_types.types[edge.type_id].allow}
            non_pedestrian_edges = adjacent_edges - pedestrian_edges

            if not non_pedestrian_edges:
                continue

            # set any nodes referencing a crossing to PRIORITY_STOP
            # this forces lanes with low priority (e.g. the crossing)
            # to wait for lanes with priority (cars)
            merged_node.type = NodeType.PRIORITY_STOP

            clusters: List[Set[Edge]] = min_cluster(
                non_pedestrian_edges,
                lambda dist: dist < 4,
                lambda e1, e2: np.min([np.linalg.norm(pt1 - pt2)
                                       for lane1 in e1.lanes
                                       for lane2 in e2.lanes
                                       for pt1 in np.array(lane1.shape)
                                       for pt2 in np.array(lane2.shape)])
            )
            crossing_lanelets = merge_lanelets(crossing_lanelets)

            crossings: List[Crossing] = []
            for edges in clusters:
                common_node: Node = reduce(lambda a, b: a & b,
                                           [{edge.from_node, edge.to_node} for edge in edges]).pop()
                assert common_node, "Edges in one cluster have to share a common node"
                # find vertices closest to the common node
                pts = np.array([vtx
                                for edge in edges
                                for lane in edge.lanes
                                for vtx in
                                [lane.shape[-1] if edge.to_node == common_node else lane.shape[0]]])
                center = np.mean(pts, axis=0)

                lanelet = crossing_lanelets[
                    int(np.argmin([np.min(np.linalg.norm(lanelet.center_vertices - center, axis=1))
                                   for lanelet in crossing_lanelets]))
                ]
                shape = lanelet.center_vertices
                c = Crossing(node=merged_node,
                             edges=edges,
                             shape=shape,
                             width=float(
                                 np.median(np.linalg.norm(lanelet.left_vertices - lanelet.right_vertices, axis=1))))
                crossings.append(c)

            new_crossings[merged_node_id] = crossings
        self._crossings = new_crossings

    def _create_traffic_lights(self):
        # tl (traffic_light_id) -> Node (Traffic Light)
        cr_traffic_lights: Dict[int, TrafficLight] = {traffic_light.traffic_light_id: traffic_light
                                                      for traffic_light in self.lanelet_network.traffic_lights}
        node_2_traffic_light: Dict[Node, Set[TrafficLight]] = defaultdict(set)
        node_2_connections: Dict[Node, Set[Connection]] = defaultdict(set)
        light_2_connections: Dict[TrafficLight, Set[Connection]] = defaultdict(set)

        for lanelet in self.lanelet_network.lanelets:
            if not lanelet.traffic_lights:
                continue
            lights: Set[TrafficLight] = {cr_traffic_lights[tl] for tl in lanelet.traffic_lights if
                                         cr_traffic_lights[tl].active}
            edge_id = self.lanelet_id2edge_id[lanelet.lanelet_id]
            if edge_id not in self.new_edges:
                logging.warning(f"Edge: {edge_id} has been removed in SUMO-NET but contained a traffic light")
                continue
            edge = self.new_edges[edge_id]
            node: Node = edge.to_node
            node_2_traffic_light[node] |= lights

            # maps each succeeding lanelet to the angle (in radians, [-pi, pi]) it forms with the preceding one
            successors: Dict[Connection, float] = dict()

            def succeeding_new_edges(edge: Edge):
                queue = edge.outgoing.copy()
                visited = set()
                res = set()
                while queue:
                    current = queue.pop()
                    if current in visited:
                        continue
                    visited.add(current)
                    if current.id in self.new_edges:
                        res.add(current)
                        continue
                    queue += current.outgoing
                return res

            for successor in succeeding_new_edges(edge):
                for connection in (c for c in self._new_connections if c.from_edge == edge and c.to_edge == successor):
                    # compute angle
                    from_dir = connection.from_lane.shape[-1] - connection.from_lane.shape[-2]
                    to_dir = connection.to_lane.shape[-1] - connection.to_lane.shape[-2]
                    angle = np.arctan2(from_dir[0] * to_dir[1] - from_dir[1] * to_dir[0],
                                       from_dir[0] * to_dir[0] + from_dir[1] * to_dir[1])
                    successors[connection] = angle

            # Angle ranges for TrafficLightDirections in radians, [-pi, pi]
            # [-pi, 0) = right, (0, pi] = left
            direction_ranges: Dict[TrafficLightDirection, Interval] = {
                TrafficLightDirection.ALL: Interval(-np.pi, np.pi),
                TrafficLightDirection.RIGHT: Interval(-np.pi, -np.pi / 4),
                TrafficLightDirection.STRAIGHT_RIGHT: Interval(-np.pi / 4, -np.pi / 8),
                TrafficLightDirection.STRAIGHT: Interval(-np.pi / 8, np.pi / 8),
                TrafficLightDirection.LEFT_STRAIGHT: Interval(np.pi / 8, np.pi / 4),
                TrafficLightDirection.LEFT: Interval(np.pi / 4, np.pi)
            }
            for light in lights:
                try:
                    if not light.direction or light.direction == TrafficLightDirection.ALL:
                        connections = set(successors.keys())
                    else:
                        connections = {l for l, angle in successors.items()
                                       if direction_ranges[light.direction].contains(angle)}
                    node_2_connections[node] |= connections
                    light_2_connections[light] |= connections
                except KeyError:
                    logging.exception(f"Unknown TrafficLightDirection: {light.direction}, "
                                      f"could not add successors for lanelet {lanelet}")

        # generate traffic lights in SUMO format
        encoder = TrafficLightEncoder(self.conf)
        for to_node, lights in node_2_traffic_light.items():
            program, connections = encoder.encode(to_node, list(lights), light_2_connections)
            self.traffic_light_signals.add_program(program)
            for connection in connections:
                self.traffic_light_signals.add_connection(connection)

    def _is_merged_edge(self, edge: Edge):
        """
        returns True if the edge must be removed, False otherwise
        :param edge: the edge to consider
        :return: flag remove_edge
        """
        start_node_id = edge.from_node.id
        end_node_id = edge.to_node.id

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

    def _calculate_centroid(self, nodes: Iterable[Node]) -> np.ndarray:
        """
        Calculate the average of a given list of nodes
        :param nodes: list containing nodes
        :return: the coordinates of the average node, x and y
        """
        return np.mean([node.coord for node in nodes], axis=0)

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
            lanelet: Lanelet = self.lanelet_network.find_lanelet_by_id(lanelet_id)
            if not lanelet:
                logging.warning("Invalid lanelet: {}".format(lanelet_id))
                return False
            # if the selected lanelet is not an incoming one, check the prececessors
            try:
                lanelet_id = next(pred for pred in lanelet.predecessor if pred in self.lanelet_id2junction)
            except StopIteration:
                logging.info("No junction found for lanelet {}".format(lanelet_id))
                return False

        # does the lanelet have predefined traffic light?
        # If so guess signals for them and copy the corresponding position
        guess_signals = False
        if self.lanelet_network.find_lanelet_by_id(lanelet_id).traffic_lights:
            guess_signals = True

        # auto generate the TLS with netconvert
        junction = self.lanelet_id2junction[lanelet_id]
        command = f"netconvert" \
                  f" --sumo-net-file={self._output_file}" \
                  f" --output-file={self._output_file}" \
                  f" --tls.guess=true" \
                  f" --tls.guess-signals={'true' if guess_signals else 'false'}" \
                  f" --tls.group-signals=true" \
                  f" --tls.cycle.time={cycle_time}" \
                  f" --tls.set={junction.id}"
        try:
            out = subprocess.check_output(command.split(), timeout=5.0, stderr=subprocess.STDOUT)
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
                if not int(tl_logic.get("id")) == junction.id:
                    continue

                tls_program = TLSProgram(tl_logic.get("programID"),
                                         int(tl_logic.get("offset")),
                                         tl_logic.get("type"))
                for phase in tl_logic.findall("phase"):
                    tls_program.add_phase(Phase(
                        int(phase.get("duration")),
                        [SignalState(s) for s in phase.get("state")]
                    ))
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
            time_offset = tls_program.offset
            direction = TrafficLightDirection.ALL
            active = True

            # replace current traffic light if one exists on the lanelet
            if lanelet.traffic_lights:
                traffic_lights: List[TrafficLight] = [self.lanelet_network.find_traffic_light_by_id(id)
                                                      for id in lanelet.traffic_lights]
                tl = traffic_lights[0]
                # copy attributes from old TrafficLight to new one
                position = tl.position
                direction = tl.direction
                active = tl.active
                # remove old traffic light from lanelet
                lanelet._traffic_lights -= {tl.traffic_light_id}

            traffic_light = TrafficLight(next_cr_id,
                                         [TrafficLightCycleElement(
                                             traffic_light_states_SUMO2CR[phase.state[link_index]],
                                             int(phase.duration / self.conf.dt))
                                             for phase in tls_program.phases],
                                         position, time_offset, direction, active)
            next_cr_id += 1

            self.lanelet_network.add_traffic_light(traffic_light,
                                                   {lanelet_id})

        remove_unreferenced_traffic_lights(self.lanelet_network)
        return True

    def write_intermediate_files(self, output_path: str) -> Tuple[str, ...]:
        """
        Function for writing the edges and nodes files in xml format
        :param output_path: the relative path of the output
        :return: None
        """

        return (self._write_nodes_file(output_path),
                self._write_edges_file(output_path),
                self._write_connections_file(output_path),
                self._write_traffic_file(output_path),
                self._write_edge_type_file(output_path))

    def _write_nodes_file(self, output_path: str) -> str:
        """
        Functio for writing the nodes file
        :param output_path: path for the file
        :return: nothing
        """
        file_path = os.path.join(os.path.dirname(output_path), f"{self.conf.scenario_name}.nod.xml")
        with open(file_path, 'w+') as output_file:
            sumolib.writeXMLHeader(output_file, 'CommonRoad Map Tool')
            nodes = etree.Element("nodes")

            for node in self.new_nodes.values():
                nodes.append(etree.fromstring(node.to_xml()))

            # pretty print & write the generated xml
            output_file.write(str(etree.tostring(nodes, pretty_print=True, encoding="utf-8"), encoding="utf-8"))

        self._nodes_file = file_path
        return file_path

    def _write_edges_file(self, output_path: str) -> str:
        """
        Function for writing the edges file
        :param output_path: path for the file
        :return: nothing
        """
        file_path = os.path.join(os.path.dirname(output_path), f"{self.conf.scenario_name}.edg.xml")
        with open(file_path, 'w+') as output_file:
            sumolib.writeXMLHeader(output_file, 'CommonRoad Map Tool')
            edges = etree.Element('edges')
            for edge in self.new_edges.values():
                edges.append(etree.fromstring(edge.to_xml()))

            # pretty print & write the generated xml
            output_file.write(str(etree.tostring(edges, pretty_print=True, encoding="utf-8"), encoding="utf-8"))

        self._edges_file = file_path
        return file_path

    def _write_connections_file(self, output_path: str) -> str:
        """
        Function for writing the connections file
        :param output_path: path for the file
        :return: nothing
        """
        file_path = os.path.join(os.path.dirname(output_path), f"{self.conf.scenario_name}.con.xml")
        with open(file_path, 'w+') as output_file:
            sumolib.writeXMLHeader(output_file, 'CommonRoad Map Tool')
            connections = etree.Element('connections')
            for connection in self._new_connections:
                connections.append(etree.fromstring(connection.to_xml()))
            for crossings in self._crossings.values():
                for crossing in crossings:
                    connections.append(etree.fromstring(crossing.to_xml()))

            # pretty print & write the generated xml
            output_file.write(str(etree.tostring(connections, pretty_print=True, encoding="utf-8"), encoding="utf-8"))

        self._connections_file = file_path
        return file_path

    def _write_traffic_file(self, output_path: str) -> str:
        """
        Writes the tll.net.xml file to disk
        :param output_path: path for the file
        """
        file_path = os.path.join(os.path.dirname(output_path), f"{self.conf.scenario_name}.tll.xml")
        with open(file_path, "w+") as f:
            sumolib.writeXMLHeader(f, 'CommonRoad Map Tool')
            xml = etree.fromstring(self.traffic_light_signals.to_xml())
            f.write(str(etree.tostring(xml, pretty_print=True, encoding="utf-8"), encoding="utf-8"))
        self._traffic_file = file_path
        return file_path

    def _write_edge_type_file(self, output_path: str) -> str:
        """
        Writes the tll.net.xml file to disk
        :param output_path: path for the file
        """
        file_path = os.path.join(os.path.dirname(output_path), f"{self.conf.scenario_name}.typ.xml")
        with open(file_path, "w+") as f:
            sumolib.writeXMLHeader(f, 'CommonRoad Map Tool')
            types = etree.fromstring(self.edge_types.to_xml())
            f.write(str(etree.tostring(types, pretty_print=True, encoding="utf-8"), encoding="utf-8"))
        self._type_file = file_path
        return file_path

    def merge_intermediate_files(self, output_path: str, nodes_path: str, edges_path: str, connections_path: str,
                                 traffic_path: str, type_path: str, cleanup=False, update_internal_ids=True) -> bool:
        """
        Function that merges the edges and nodes files into one using netconvert
        :param connections_path:
        :param nodes_path:
        :param edges_path:
        :param traffic_path:
        :param type_path:
        :param output_path: the relative path of the output
        :param cleanup: deletes temporary input files after creating net file (only deactivate for debugging)
        :param update_internal_ids: Updates the internal Edge IDs from the newly generated net file
        :return: bool: returns False if conversion fails
        """

        # The header of the xml files must be removed
        to_remove = ["options", "xml"]
        for path in [nodes_path, edges_path, connections_path, traffic_path]:
            # Removing header in file
            with open(path, 'r') as file:
                lines = file.readlines()
            with open(path, 'w') as file:
                for line in lines:
                    if not any(word in line for word in to_remove):
                        file.write(line)

        self._output_file = str(output_path)
        # Calling of Netconvert
        command = f"netconvert " \
                  f" --no-turnarounds=true" \
                  f" --junctions.internal-link-detail=20" \
                  f" --geometry.avoid-overlap=true" \
                  f" --geometry.remove.keep-edges.explicit=true" + \
                  f" --offset.disable-normalization=true" \
                  f" --node-files={nodes_path}" \
                  f" --edge-files={edges_path}" \
                  f" --connection-files={connections_path}" \
                  f" --tllogic-files={traffic_path}" \
                  f" --type-files={type_path}" \
                  f" --output-file={output_path}" \
                  f" --seed={SumoConfig.random_seed}"
        success = True
        try:
            _ = subprocess.check_output(command.split(), timeout=5.0)
            self._read_junctions_from_net_file(self._output_file)
            # update lengths
            update_edge_lengths(self._output_file)

            if update_internal_ids:
                self._update_internal_IDs_from_net_file(self._output_file)

        except FileNotFoundError as e:
            if 'netconvert' in e.filename:
                warnings.warn("Is netconvert installed and added to PATH?")
            success = False
        except ScenarioException:
            raise
        except Exception as e:
            logging.exception(e)
            success = False

        if cleanup and success:
            for path in [nodes_path, edges_path, connections_path, traffic_path]:
                os.remove(path)

        return success

    def _update_internal_IDs_from_net_file(self, net_file_path: str):
        with open(net_file_path, 'r') as f:
            root = ET.parse(f)

        def grouped_list(list, criterion):
            return groupby(sorted(list, key=criterion), key=criterion)

        original_connection_map = {str(from_edge):
                                       {str(from_lane.split("_")[-1]):
                                            {str(to_edge):
                                                 {str(to_lane.split("_")[-1]):
                                                      [connection.via for connection in to_lane_connections]
                                                  for to_lane, to_lane_connections in grouped_list(to_edge_connections,
                                                                                                   lambda
                                                                                                       c: c.to_lane.id)}
                                             for to_edge, to_edge_connections in grouped_list(from_lane_connections,
                                                                                              lambda c: c.to_edge.id)}
                                        for from_lane, from_lane_connections in grouped_list(from_edge_connections,
                                                                                             lambda c: c.from_lane.id)}
                                   for from_edge, from_edge_connections in grouped_list(self._new_connections,
                                                                                        lambda c: c.from_edge.id)}

        available_lane_ids = set()

        for connection_xml in root.findall("connection"):
            from_edge_id = connection_xml.get('from')
            to_edge_id = connection_xml.get('to')

            from_lane_id = connection_xml.get('fromLane')
            to_lane_id = connection_xml.get('toLane')

            # Add seen lane ids to the available set
            available_lane_ids |= {f"{from_edge_id}_{from_lane_id}", f"{to_edge_id}_{to_lane_id}"}

            # Skip the connections from or to internal edges
            if from_edge_id.startswith(':') or to_edge_id.startswith(':'):
                continue

            # Skip the normal connection
            new_internal_connection_id = connection_xml.get('via')
            if not new_internal_connection_id or not new_internal_connection_id.startswith(':'):
                continue

            # if new_internal_connection_ID.contains(' '):
            #     raise ScenarioException("There is no lanelet between intersections/junctions, which causes that these intersections must be merged in SUMO, therefore multiple internal edges would be in this merged intersection, which is not supported!")

            new_internal_connection_id_split = new_internal_connection_id.split('_')
            new_internal_edge_id = f"{new_internal_connection_id_split[0]}_{new_internal_connection_id_split[1]}"
            new_internal_lane_id = int(new_internal_connection_id_split[2])

            try:
                original_internal_connection_ids = \
                    original_connection_map[from_edge_id][from_lane_id][to_edge_id][to_lane_id]
            except KeyError as invalid_key:
                raise ScenarioException(
                    f"Inconsistent scenario, there is no connection between "
                    f"from: {from_edge_id}_{from_lane_id}, to: {to_edge_id}_{to_lane_id}, {invalid_key}")

            if len(original_internal_connection_ids) > 1:
                raise RuntimeError(
                    f"The connection is ambiguous between from {from_edge_id}_{from_lane_id}, to {to_edge_id}_{to_lane_id}")
            original_internal_connection_ids = original_internal_connection_ids[0]

            # If there is no internal connection, continue
            if original_internal_connection_ids is None:
                continue

            for original_internal_connection_ID in original_internal_connection_ids:
                original_internal_connection_ID_splitted = original_internal_connection_ID.split('_')
                original_internal_edge_ID = original_internal_connection_ID_splitted[0]
                original_internal_lane_ID = original_internal_connection_ID_splitted[1]

                original_lanelet_ID = self.lane_id2lanelet_id[original_internal_connection_ID]

                # Update the dictionaries
                if new_internal_connection_id in self.lane_id2lanelet_id:
                    if not isinstance(self.lane_id2lanelet_id[new_internal_connection_id], list):
                        self.lane_id2lanelet_id[new_internal_connection_id] = [
                            self.lane_id2lanelet_id[new_internal_connection_id]]
                    self.lane_id2lanelet_id[new_internal_connection_id].append(original_lanelet_ID)
                else:
                    self.lane_id2lanelet_id[new_internal_connection_id] = original_lanelet_ID
                # del self.lane_id2lanelet_id[original_internal_connection_ID]
                self.lanelet_id2edge_id[original_lanelet_ID] = new_internal_edge_id
                self.lanelet_id2edge_lane_id[original_lanelet_ID] = new_internal_lane_id
                self.lanelet_id2lane_id[original_lanelet_ID] = new_internal_connection_id

        # available_lanelet_ids = {self.lane_id2lanelet_id[available_lane_id] for available_lane_id in available_lane_ids if available_lane_id in self.lane_id2lanelet_id}

        for lanelet in self.lanelet_network.lanelets:
            lanelet_id = lanelet.lanelet_id
            lane_id = self.lanelet_id2lane_id[lanelet_id]
            if lane_id not in available_lane_ids:
                del self.lanelet_id2edge_id[lanelet_id]
                del self.lanelet_id2edge_lane_id[lanelet_id]
                del self.lanelet_id2lane_id[lanelet_id]

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
            shape = np.array([
                [float(i) for i in s.split(",")]
                for s in junction_xml.get('shape').split()
            ])
            junction = Junction(id=int(junction_xml.get('id')),
                                j_type=junction_xml.get('type'),
                                x=float(junction_xml.get('x')),
                                y=float(junction_xml.get('y')),
                                inc_lanes=inc_lanes,
                                shape=shape)
            for lanelet_id in [self.lane_id2lanelet_id[l.id] for l in inc_lanes]:
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

    def convert_to_net_file(self, output_folder: str) -> bool:
        """
        Convert the Commonroad scenario to a net.xml file, specified by the absolute  path output_file.
        NOTE: This method regenerates the traffic!
        :param path of the returned net.xml file
        :return returns whether conversion was successful
        """

        output_path = os.path.join(output_folder, self.conf.scenario_name + '.net.xml')
        logging.info("Converting to SUMO Map")
        self._convert_map()

        logging.info("Merging Intermediate Files")
        intermediary_files = self.write_intermediate_files(output_path)
        conversion_possible = self.merge_intermediate_files(output_path, *intermediary_files)
        if not conversion_possible:
            logging.error("Error converting map, see above for details")
            return False

        logging.info("Generating Traffic Routes")
        return self._generate_routes(output_path)

    def convert_scenario_to_net_file(self, scenario: Scenario, output_folder: str) -> bool:
        """
        Convert the Commonroad scenario to SUMO format.
        The routes will be initialized according to the trajectories defined in the CR scenario
        :param scenario: the scenario to be converted
        :param output_folder: path to the output folder
        :return returns whether conversion was successful
        """
        output_path = os.path.join(output_folder, self.conf.scenario_name + '.net.xml')
        logging.info("Converting to SUMO Map")
        self._convert_map()

        logging.info("Merging Intermediate Files")
        intermediary_files = self.write_intermediate_files(output_path)
        conversion_possible = self.merge_intermediate_files(output_path, *intermediary_files,
                                                            update_internal_ids=True)
        if not conversion_possible:
            logging.error("Error converting map, see above for details")
            return False

        logging.info("Converting Traffic Routes")
        return self._convert_routes(scenario, output_folder)

    def _convert_routes(self, scenario: Scenario, output_folder: str) -> bool:
        """
        Convert the Commonroad trajectories to SUMO routes. Next to the route files add file will be created as well
        :param scenario: the scenario to be converted
        :param output_folder: path to the output folder
        :return returns whether conversion was successful
        """
        scenario_name = self.conf.scenario_name
        net_file = os.path.join(output_folder, scenario_name + '.net.xml')

        add_file = self._convert_to_add_file(scenario, output_folder)
        rou_files = self._convert_to_rou_file(scenario, output_folder)
        self.sumo_cfg_file = self._generate_cfg_file(scenario_name, net_file, rou_files, add_file,
                                                     output_folder)
        return True

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

        scenario_name = self.conf.scenario_name
        out_folder = os.path.dirname(net_file)

        add_file = self._generate_add_file(scenario_name, out_folder)
        rou_files = self._generate_rou_file(net_file, scenario_name,
                                            out_folder)
        self.sumo_cfg_file = self._generate_cfg_file(scenario_name, net_file,
                                                     rou_files, add_file,
                                                     out_folder)
        return True

    def _convert_to_add_file(self, scenario: Scenario, output_folder: str) -> str:
        """
        During converting the Commonroad trajectories to SUMO routes add file is required for SUMO.
        :param scenario: the scenario to be converted
        :param output_folder: path to the output folder
        :return: the path of the created add file
        """
        add_file = os.path.join(output_folder, self.conf.scenario_name + '.add.xml')

        # create file
        domTree = minidom.Document()
        additional_node = domTree.createElement("additional")
        domTree.appendChild(additional_node)
        vType_dist_node = domTree.createElement("vTypeDistribution")
        vType_dist_node.setAttribute("id", "DEFAULT_VEHTYPE")
        additional_node.appendChild(vType_dist_node)

        # config parameters for easy access
        vehicle_params = self.conf.veh_params
        driving_params = self.conf.driving_params

        def get_grouped_obstacles(obstacle_list):
            return {obstacle_id: list(obstacles)
                    for obstacle_id, obstacles in groupby(sorted(obstacle_list,
                                                                 key=lambda
                                                                     obstacle: obstacle.obstacle_type.value),
                                                          key=lambda
                                                              obstacle: obstacle.obstacle_type)}

        num_all_obstacles = len(scenario.obstacles)
        grouped_obstacles = {ObstacleRole.STATIC: get_grouped_obstacles(scenario.static_obstacles),
                             ObstacleRole.DYNAMIC: get_grouped_obstacles(
                                 scenario.dynamic_obstacles)}

        for veh_role, type_grouped_obstacles in grouped_obstacles.items():
            for veh_type, obstacle_list in type_grouped_obstacles.items():
                try:
                    sumo_veh_type = VEHICLE_TYPE_CR2SUMO[veh_type]
                    if veh_role == ObstacleRole.STATIC:
                        sumo_veh_type_name = sumo_veh_type.value + "_static"
                    else:
                        sumo_veh_type_name = sumo_veh_type.value
                except KeyError:
                    logging.warning(f"{veh_type} could not be converted to SUMO")
                    continue
                vType_node = domTree.createElement("vType")
                vType_node.setAttribute("id", sumo_veh_type_name)
                vType_node.setAttribute("guiShape", sumo_veh_type)
                vType_node.setAttribute("vClass", sumo_veh_type)
                vType_node.setAttribute("probability", str(len(obstacle_list) / num_all_obstacles))

                for att_name, setting in vehicle_params.items():
                    att_value = setting[sumo_veh_type]
                    if type(att_value) is Interval:
                        raise ValueError(
                            f"Converting a CommonRoad scenario does not support using Interval "
                            f"as value for parameter {att_name}.{veh_type}")
                    else:
                        att_value = str(att_value)
                    vType_node.setAttribute(att_name, att_value)
                for att_name, att_value in driving_params.items():
                    vType_node.setAttribute(att_name, str("{0:.2f}".format(att_value)))
                if veh_role == ObstacleRole.STATIC:
                    vType_node.setAttribute("maxSpeed", str(f"{sys.float_info.min}"))

                vType_dist_node.appendChild(vType_node)

        with open(add_file, "w") as f:
            domTree.documentElement.writexml(f, addindent="\t", newl="\n")

        logging.info("Additional file written to {}".format(add_file))
        return add_file

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
                vType_node.setAttribute("id", VEHICLE_TYPE_CR2SUMO[veh_type].value)
                vType_node.setAttribute("guiShape", VEHICLE_TYPE_CR2SUMO[veh_type].value)
                vType_node.setAttribute("vClass", VEHICLE_TYPE_CR2SUMO[veh_type].value)
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

    def _convert_to_rou_file(
        self,
        scenario: Scenario,
        out_folder: str,
    ) -> Dict[str, str]:
        """
        Creates route files from CommonRoad scenario.

        :param scenario: the scenario to be converted
        :param out_folder: output folder of route file
        :return: path of route file
        """

        ccosy_cache = {}

        def get_ccosy(lanelet: Lanelet):
            if lanelet.lanelet_id not in ccosy_cache:
                ccosy_cache[lanelet.lanelet_id] = create_coordinate_system_from_polyline(
                    lanelet.center_vertices)
            return ccosy_cache[lanelet.lanelet_id]

        # TODO: The following methods are coming from the route-planner repository.
        #  These functions are currently required only for this method, however, this functionality
        #  is useful over the whole CommonRoad framework, therefore it should be placed
        #  in the pycrccosy or commonroad-io repository
        #  The future of these methods needs to be discussed
        def relative_orientation(from_angle1_in_rad, to_angle2_in_rad):
            phi = (to_angle2_in_rad - from_angle1_in_rad) % (2 * np.pi)
            if phi > np.pi:
                phi -= (2 * np.pi)

            return phi

        def lanelet_orientation_at_position(lanelet: Lanelet, position: np.ndarray):
            """
            Finds the lanelet orientation with the two closest point to the given state

            :param lanelet: Lanelet on which the orientation at the given state should be calculated
            :param position: Position where the lanelet's orientation should be calculated
            :return: An orientation in interval [-pi,pi]
            """
            ccosy = get_ccosy(lanelet)
            long, rel_pos_to_domain = get_long_dist(ccosy, position)
            tangent = ccosy.tangent(long)
            return np.arctan2(tangent[1], tangent[0])

        def sorted_lanelet_ids(lanelet_ids: List[int], orientation: float, position: np.ndarray,
                               scenario: Scenario) \
            -> List[int]:
            """
            return the lanelets sorted by relative orientation to the position and orientation given
            """

            if len(lanelet_ids) <= 1:
                return lanelet_ids
            else:
                lanelet_id_list = np.array(lanelet_ids)

                def get_lanelet_relative_orientation(lanelet_id):
                    lanelet = scenario.lanelet_network.find_lanelet_by_id(lanelet_id)
                    lanelet_orientation = lanelet_orientation_at_position(lanelet, position)
                    return np.abs(relative_orientation(lanelet_orientation, orientation))

                orientation_differences = np.array(
                    list(map(get_lanelet_relative_orientation, lanelet_id_list)))
                sorted_indices = np.argsort(orientation_differences)
                return list(lanelet_id_list[sorted_indices])

        def create_coordinate_system_from_polyline(
            polyline) -> pycrccosy.CurvilinearCoordinateSystem:

            def compute_polyline_length(polyline: np.ndarray) -> float:
                """
                Computes the path length s of a given polyline
                :param polyline: The polyline
                :return: The path length of the polyline
                """
                assert isinstance(polyline, np.ndarray) and polyline.ndim == 2 and len(
                    polyline[:,
                    0]) > 2, 'Polyline malformed for path length computation p={}'.format(polyline)

                distance_between_points = np.diff(polyline, axis=0)
                # noinspection PyTypeChecker
                return np.sum(np.sqrt(np.sum(distance_between_points ** 2, axis=1)))

            def resample_polyline_with_length_check(polyline):
                length = np.linalg.norm(polyline[-1] - polyline[0])
                if length > 2.0:
                    polyline = resample_polyline(polyline, 1.0)
                else:
                    polyline = resample_polyline(polyline, length / 10.0)

                return polyline

            def chaikins_corner_cutting2(coords, refinements=2):
                coords = np.array(coords)

                for _ in range(refinements):
                    L = coords.repeat(2, axis=0)
                    R = np.empty_like(L)
                    R[0] = L[0]
                    R[2::2] = L[1:-1:2]
                    R[1:-1:2] = L[2::2]
                    R[-1] = L[-1]
                    coords = L * 0.75 + R * 0.25

                return coords

            polyline = resample_polyline_with_length_check(polyline)

            abs_curvature = abs(compute_curvature_from_polyline(polyline))
            max_curvature = max(abs_curvature)
            infinite_loop_counter = 0
            while max_curvature > 0.1:
                polyline = np.array(chaikins_corner_cutting2(polyline))

                length = compute_polyline_length(polyline)
                if length > 10:
                    polyline = resample_polyline(polyline, 1.0)
                else:
                    polyline = resample_polyline(polyline, length / 10.0)

                abs_curvature = abs(compute_curvature_from_polyline(polyline))
                max_curvature = max(abs_curvature)

                infinite_loop_counter += 1

                if infinite_loop_counter > 20:
                    break

            return pycrccosy.CurvilinearCoordinateSystem(polyline)

        def get_long_dist(ccosy, position):
            try:
                rel_pos_to_domain = 0
                long_dist, lat_dist = ccosy.convert_to_curvilinear_coords(position[0], position[1])
                return long_dist, rel_pos_to_domain
            except ValueError:
                eps = 0.1
                curvi_coords_of_projection_domain = np.array(ccosy.curvilinear_projection_domain())

                longitudinal_min, normal_min = np.min(curvi_coords_of_projection_domain,
                                                      axis=0) + eps
                longitudinal_max, normal_max = np.max(curvi_coords_of_projection_domain,
                                                      axis=0) - eps
                normal_center = (normal_min + normal_max) / 2

                bounding_points = np.array(
                    [ccosy.convert_to_cartesian_coords(longitudinal_min, normal_center),
                     ccosy.convert_to_cartesian_coords(longitudinal_max, normal_center)])
                rel_positions = position - np.array(
                    [bounding_point for bounding_point in bounding_points])
                distances = np.linalg.norm(rel_positions, axis=1)

                if distances[0] < distances[1]:
                    # Nearer to the first bounding point
                    rel_pos_to_domain = -1
                    return 0, rel_pos_to_domain
                else:
                    # Nearer to the last bounding point
                    rel_pos_to_domain = 1
                    return ccosy.length(), rel_pos_to_domain

        def find_lanelet_id(state: State):
            possible_lanelet_ids = \
                scenario.lanelet_network.find_lanelet_by_position([state.position])[0]

            if len(possible_lanelet_ids) == 0:
                possible_lanelet_ids = scenario.lanelet_network.find_lanelet_by_shape(
                    obstacle.occupancy_at_time(state.time_step).shape)

            sorted_lanelet_id_list = sorted_lanelet_ids(possible_lanelet_ids,
                                                        state.orientation, state.position,
                                                        scenario)
            if len(sorted_lanelet_id_list) == 0:
                return None
            return sorted_lanelet_id_list[0]

        def get_position_in_lane(lanelet_id, position):
            # If the lanelet is merged in one SUMO lane, the lanelets must be merged too
            lane_id = self.lanelet_id2lane_id[lanelet_id]
            merged_lanelet_ids = self.lane_id2lanelet_id[lane_id]
            if isinstance(merged_lanelet_ids, list):
                starting_lanelet = scenario.lanelet_network.find_lanelet_by_id(merged_lanelet_ids[0])
                for succ_lanelet_id in merged_lanelet_ids[1:]:
                    succ_lanelet = scenario.lanelet_network.find_lanelet_by_id(succ_lanelet_id)
                    starting_lanelet = Lanelet.merge_lanelets(starting_lanelet, succ_lanelet)
            else:
                starting_lanelet = scenario.lanelet_network.find_lanelet_by_id(lanelet_id)
            # In SUMO the starting point of the vehicle is used as position, not the center
            depart_pos, _ = get_long_dist(get_ccosy(starting_lanelet), position)
            depart_pos += sumo_veh_length_center

            return depart_pos

        grouped_obstacles = {k: list(g) for k, g in groupby(sorted(scenario.obstacles,
                                                                   key=lambda
                                                                       obstacle: obstacle.obstacle_type.value),
                                                            key=lambda
                                                                obstacle: obstacle.obstacle_type)}

        # filenames
        route_files: Dict[str, str] = {
            'vehicle': os.path.join(out_folder, self.conf.scenario_name + ".vehicles.rou.xml"),
            "pedestrian": os.path.join(out_folder, self.conf.scenario_name + ".pedestrians.rou.xml")
        }

        for route_type, route_file in route_files.items():
            flatten = lambda l: [item for sublist in l for item in sublist]
            route_obstacles = flatten([obstacles
                                       for obstacle_type, obstacles in grouped_obstacles.items()
                                       if VEHICLE_NODE_TYPE_CR2SUMO[obstacle_type] == route_type])

            domTree = minidom.Document()
            routes_node = domTree.createElement("routes")
            domTree.appendChild(routes_node)
            vType_dist_node = domTree.createElement("vTypeDistribution")
            vType_dist_node.setAttribute("id", "DEFAULT_VEHTYPE")

            for obstacle in route_obstacles:
                vehicle_node = domTree.createElement("vehicle")

                vehicle_node.setAttribute("id", str(obstacle.obstacle_id))

                sumo_veh_type = VEHICLE_TYPE_CR2SUMO[obstacle.obstacle_type].value
                sumo_veh_length_center = self.conf.veh_params['length'][sumo_veh_type] / 2

                if obstacle.obstacle_role == ObstacleRole.STATIC:
                    vehicle_node.setAttribute("depart", str(scenario.dt))
                    vehicle_node.setAttribute("departSpeed", str(0))
                    vehicle_node.setAttribute("type", f"{sumo_veh_type}_static")

                    starting_lanelet_id = find_lanelet_id(obstacle.initial_state)
                    if starting_lanelet_id not in self.lanelet_id2edge_lane_id:
                        logging.warning(f"The used starting lanelet {starting_lanelet_id} of the static obstacle "
                                        f"{obstacle.obstacle_id} was not converted into the SUMO map, the obstacle will be skipped!")
                        continue
                    depart_lane = self.lanelet_id2edge_lane_id[starting_lanelet_id]
                    vehicle_node.setAttribute("departLane", str(depart_lane))

                    depart_pos = get_position_in_lane(starting_lanelet_id, obstacle.initial_state.position)
                    vehicle_node.setAttribute("departPos", str(depart_pos))

                    vehicle_route_node = domTree.createElement("route")
                    edge = str(self.lanelet_id2edge_id[starting_lanelet_id])
                    vehicle_route_node.setAttribute("edges", edge)
                    vehicle_node.appendChild(vehicle_route_node)

                    routes_node.appendChild(vehicle_node)

                elif obstacle.obstacle_role == ObstacleRole.DYNAMIC:
                    if obstacle.prediction is None:
                        raise ScenarioException(
                            f"Obstacle {obstacle.obstacle_id} in scenario {scenario.scenario_id} "
                            f"has no trajectory")

                    vehicle_node.setAttribute("depart",
                                              str(
                                                  obstacle.prediction.initial_time_step * scenario.dt))
                    vehicle_node.setAttribute("departSpeed", str(obstacle.initial_state.velocity))
                    vehicle_node.setAttribute("type", sumo_veh_type)

                    lanelet_ids = []
                    last_lanelet_id = None

                    if not isinstance(obstacle.prediction, TrajectoryPrediction):
                        raise ScenarioException(
                            f"Only scenario with TrajectoryPrediction is supported for rou file generation, "
                            f"the current obstacle was {type(obstacle.prediction)}")

                    skip_obstacle = False
                    for state in obstacle.prediction.trajectory.state_list:

                        lanelet_id = find_lanelet_id(state)
                        if lanelet_id is None:
                            logging.warning(
                                "Skipping obstacle %s, because left the lanelet network in the scenario %s",
                                obstacle.obstacle_id, scenario.scenario_id)
                            skip_obstacle = True
                            break

                        if lanelet_id != last_lanelet_id:
                            if last_lanelet_id is not None:
                                prev_lanelet = scenario.lanelet_network.find_lanelet_by_id(last_lanelet_id)
                                if len(prev_lanelet.successor) == 0:
                                    break
                                if lanelet_id not in prev_lanelet.successor:
                                    if len(prev_lanelet.successor) == 1:
                                        logging.warning(
                                            f"The lanelet ID {lanelet_id} of the state at timestep {state.time_step} of obstacle {obstacle.obstacle_id} "
                                            f"was not found within the successors {prev_lanelet.successor} of the previous state, using {prev_lanelet.successor[0]}")
                                        lanelet_id = prev_lanelet.successor[0]
                                    else:
                                        continue
                            lanelet_ids.append(lanelet_id)
                            last_lanelet_id = lanelet_id

                    if skip_obstacle:
                        continue

                    # Add one successor to force the obstacle to leave the lanelet
                    last_lanelet = scenario.lanelet_network.find_lanelet_by_id(lanelet_ids[-1])
                    if len(last_lanelet.successor) > 0:
                        lanelet_ids.append(last_lanelet.successor[0])

                    # Add successors until not ending in internal edge
                    while lanelet_ids[-1] in self.lanelet_id2edge_id and \
                        str(self.lanelet_id2edge_id[lanelet_ids[-1]]).startswith(':'):
                        last_lanelet = scenario.lanelet_network.find_lanelet_by_id(lanelet_ids[-1])
                        lanelet_ids.append(last_lanelet.successor[0])
                        # _, all_successor_lanelet_ids = Lanelet.all_lanelets_by_merging_successors_from_lanelet(
                        #     last_lanelet,
                        #     scenario.lanelet_network)
                        #
                        # successor_lanelet_ids = all_successor_lanelet_ids[0]
                        # lanelet_ids.extend(successor_lanelet_ids[1:])

                    # Remove all the not converted lanelets
                    lanelet_ids_tmp = [lanelet_id for lanelet_id in lanelet_ids if
                                       lanelet_id in self.lanelet_id2edge_id]

                    if len(lanelet_ids_tmp) == 0:
                        logging.warning(
                            f"None of the used lanelets of the vehicle {obstacle.obstacle_id} has been converted, original lanelet IDs was: {lanelet_ids}, the vehicle will be skipped")
                        continue
                    lanelet_ids = lanelet_ids_tmp

                    starting_lanelet_id = lanelet_ids[0]
                    depart_lane = self.lanelet_id2edge_lane_id[starting_lanelet_id]
                    vehicle_node.setAttribute("departLane", str(depart_lane))

                    depart_pos = get_position_in_lane(starting_lanelet_id, obstacle.initial_state.position)
                    vehicle_node.setAttribute("departPos", str(depart_pos))

                    vehicle_route_node = domTree.createElement("route")
                    edges = [str(self.lanelet_id2edge_id[lanelet_id]) for lanelet_id in lanelet_ids]
                    # Remove internal edges
                    if edges[0].startswith(':'):
                        idx = next(idx for idx, (current_edge, next_edge) in enumerate(zip(edges[0:-1], edges[1:])) if
                                   not next_edge.startswith(':'))
                    else:
                        idx = 0
                    filtered_edges = [edges[idx]]
                    filtered_edges.extend([edge_id for edge_id in edges[idx + 1:] if not edge_id.startswith(':')])

                    vehicle_route_node.setAttribute("edges", " ".join(filtered_edges))
                    vehicle_node.appendChild(vehicle_route_node)

                    routes_node.appendChild(vehicle_node)
                else:
                    logging.warning("Obstacle %s in scenario %s has unknown role %s, "
                                    "skipping this obstacle",
                                    obstacle.obstacle_id, scenario.scenario_id,
                                    obstacle.obstacle_role)

            with open(route_file, "w") as f:
                domTree.documentElement.writexml(f, addindent="\t", newl="\n")

            logging.info("Route file written to {}".format(route_file))

        return route_files

    def _generate_rou_file(
        self,
        net_file: str,
        scenario_name: str,
        out_folder: str = None,
    ) -> Dict[str, str]:
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
            'vehicle': os.path.join(out_folder, scenario_name + ".vehicles.rou.xml"),
            "pedestrian": os.path.join(out_folder, scenario_name + ".pedestrians.rou.xml")
        }
        trip_files: Dict[str, str] = {
            'vehicle': os.path.join(out_folder, scenario_name + '.vehicles.trips.xml'),
            'pedestrian': os.path.join(out_folder, scenario_name + '.pedestrian.trips.xml')
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
            str(1 - self.conf.veh_distribution[ObstacleType.PEDESTRIAN]),
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
        vehicles = sumolib.output.parse_fast(rou_file, 'vehicle', ['id', 'depart'])
        dep_times = []
        veh_ids = []
        for veh in vehicles:
            veh_ids.append(veh[0])
            dep_times.append(int(float(veh[1])))

        if n_ego_vehicles > len(veh_ids):
            warnings.warn('only {} vehicles in route file instead of {}'.format(len(veh_ids), n_ego_vehicles),
                          stacklevel=1)
            n_ego_vehicles = len(veh_ids)

        # check if specified ids exist
        for i in self.conf.ego_ids:
            if i not in veh_ids:
                warnings.warn('<generate_rou_file> id {} not in route file!'.format_map(i))
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
            '*/net-file': os.path.basename(net_file),
            '*/route-files': ",".join([os.path.basename(f) for f in route_files.values()]),
            '*/additional-files': os.path.basename(add_file),
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

    def draw_network(self, nodes: List[Node], edges: List[Edge], figsize=(20, 20)):
        plt.figure(figsize=figsize)

        G = nx.DiGraph()
        graph_nodes = [node.id for node in nodes]
        graph_nodes_pos = {node.id: node.coord for node in nodes}
        for edge in edges:
            G.add_edge(edge.from_node.id, edge.to_node.id, label=edge.id)
        G.add_nodes_from(graph_nodes)
        nx.draw(G, graph_nodes_pos, with_labels=True)
        colors = itertools.cycle(set(mcolors.TABLEAU_COLORS) - {"tab:blue"})
        for cluster in self.merged_dictionary.values():
            nx.draw_networkx_nodes(G, graph_nodes_pos, nodelist=cluster, node_color=next(colors))
        labels = nx.get_edge_attributes(G, "label")
        nx.draw_networkx_edge_labels(G, pos=graph_nodes_pos, edge_labels=labels)
        plt.autoscale()
        plt.show()
