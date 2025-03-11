"""This class contains functions for converting a CommonRoad map into a .net.xml SUMO map"""

import itertools
import logging
import os
import subprocess
import sys
import warnings
from collections import defaultdict
from copy import deepcopy
from functools import lru_cache, reduce
from itertools import groupby
from typing import Dict, Iterable, List, Optional, Set, Tuple

# TODO: Move to a single XML lib
from xml.dom import minidom
from xml.etree import cElementTree as ET

import lxml.etree as etree
import matplotlib.colors as mcolors
import networkx as nx
import numpy as np
import sumolib
from commonroad.common.solution import VehicleType as VehicleTypeParam
from commonroad.common.util import Interval
from commonroad.prediction.prediction import TrajectoryPrediction
from commonroad.scenario.intersection import Intersection
from commonroad.scenario.lanelet import (
    Lanelet,
    LaneletNetwork,
    LaneletType,
    LineMarking,
)
from commonroad.scenario.obstacle import ObstacleRole, ObstacleType
from commonroad.scenario.scenario import Scenario
from commonroad.scenario.traffic_light import (
    TrafficLight,
    TrafficLightCycle,
    TrafficLightCycleElement,
    TrafficLightDirection,
)
from commonroad.scenario.traffic_sign import SupportedTrafficSignCountry, TrafficSign
from commonroad.scenario.traffic_sign_interpreter import TrafficSignInterpreter
from commonroad.scenario.trajectory import State
from commonroad.visualization.mp_renderer import MPRenderer
from commonroad_clcs.clcs import CurvilinearCoordinateSystem
from commonroad_clcs.config import CLCSParams
from commonroad_clcs.util import (
    compute_curvature_from_polyline,
    resample_polyline,
)
from commonroad_dc.costs.route_matcher import LaneletRouteMatcher
from matplotlib import pyplot as plt
from shapely.geometry import LineString, Point
from sumocr.scenario.abstract_scenario_wrapper import AbstractScenarioWrapper

from crdesigner.common.file_reader import CRDesignerFileReader
from crdesigner.map_conversion.sumo_map.config import SumoConfig
from crdesigner.map_conversion.sumo_map.errors import ScenarioException
from crdesigner.map_conversion.sumo_map.sumolib_net import (
    TLS,
    Connection,
    Crossing,
    Edge,
    Junction,
    Lane,
    Net,
    Node,
    NodeType,
    RightOfWay,
    Roundabout,
    SpreadType,
    VehicleType,
    sumo_net_from_xml,
)
from crdesigner.map_conversion.sumo_map.util import (
    _find_intersecting_edges,
    get_total_lane_length_from_netfile,
    max_lanelet_network_id,
    merge_lanelets,
    min_cluster,
    update_edge_lengths,
)

from .mapping import (
    DEFAULT_CFG_FILE,
    VEHICLE_NODE_TYPE_CR2SUMO,
    VEHICLE_TYPE_CR2SUMO,
    ClusterInstruction,
    directions_SUMO2CR,
    get_edge_types_from_template,
    get_sumo_edge_type,
    traffic_light_states_SUMO2CR,
)
from .traffic_light import TrafficLightEncoder
from .traffic_sign import TrafficSignEncoder

# This file is used as a template for the generated .sumo.cfg files


class CR2SumoMapConverter(AbstractScenarioWrapper):
    """Converts CommonRoad map to sumo map .net.xml"""

    def __init__(self, scenario: Scenario, conf: SumoConfig):
        """
        :param scenario: CommonRoad Scenario to be converted
        :param conf: configuration file for additional map conversion parameters
        """
        self.initial_scenario: Scenario = scenario
        self.conf: SumoConfig = conf
        self.country_id = (
            SupportedTrafficSignCountry(conf.country_id)
            if isinstance(conf.country_id, str)
            else conf.country_id
        )
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
        # collect which lanelet ids are prohibited by a lanelet
        self.prohibits = defaultdict(list)
        # dict of merged_node_id and Crossing
        self._crossings: Dict[int, Set[Lanelet]] = dict()
        # key is the ID of the edges and value the ID of the lanelets that compose it
        self.lanes_dict: Dict[int, List[int]] = {}
        # lane ID -> Lane
        self.lanes: Dict[str, Lane] = {}
        # edge_id -> length (float)
        self.edge_lengths: Dict[str, float] = {}
        # list of the already explored lanelets
        self._explored_lanelets = []
        self._max_vehicle_width = max(self.conf.veh_params["width"].values())

        # traffic signs
        self._traffic_sign_interpreter: TrafficSignInterpreter = TrafficSignInterpreter(
            self.country_id, self.lanelet_network
        )
        # Read Edge Types from template
        self.edge_types = get_edge_types_from_template(self.country_id)

        self.lane_id2lanelet_id: Dict[str, int] = {}
        self.lanelet_id2lane_id: Dict[int, str] = {}
        self.lanelet_id2edge_id: Dict[int, int] = {}
        self.lanelet_id2edge_lane_id: Dict[int, int] = {}
        self.roundabouts: List[Roundabout] = []
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
        self._additional_file = ""
        # path to SUMO typ.xml file
        self._type_file = ""
        self._output_file = ""

        # simulation params
        self.scenario_name = ""
        self.sumo_cfg_file = ""
        self.ego_start_time = self.conf.ego_start_time
        self.logger = self._init_logging()
        self.logger.setLevel(self.conf.logging_level)

    def _init_logging(self):
        # Create a custom logger
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(level=getattr(logging, self.conf.logging_level))

        if not logger.hasHandlers():
            # Create handlers
            c_handler = logging.StreamHandler()

            # Create formatters and add it to handlers
            c_format = logging.Formatter("<%(name)s.%(funcName)s:%(lineno)d> %(message)s")
            c_handler.setFormatter(c_format)

            # Add handlers to the logger
            logger.addHandler(c_handler)

        return logger

    @classmethod
    def from_file(cls, file_path_cr, conf: SumoConfig):
        scenario, _ = CRDesignerFileReader(file_path_cr).open()
        return cls(scenario, conf)

    def _convert_map(self):
        self._find_lanes()
        self._init_nodes()
        self._create_sumo_edges_and_lanes()
        self._init_connections()
        self.new_nodes, self.merged_dictionary, replaced_nodes = (
            self._merge_junctions_intersecting_lanelets()
        )
        self.logger.info(f"Merged: {self.merged_dictionary}")
        self.new_edges = self._filter_edges(self.merged_dictionary, replaced_nodes)
        self._create_lane_based_connections()
        # self._set_prohibited_connections()
        self.roundabouts = self._create_roundabouts()
        # self._create_crossings()
        self._encode_traffic_signs()
        self._create_traffic_lights()

    def _find_lanes(self):
        """
        Convert a CommonRoad net into a SUMO net
        sumo_net contains the converted net
        """

        self._points_dict = {
            lanelet.lanelet_id: lanelet.center_vertices for lanelet in self.lanelet_network.lanelets
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
            while adj_right_id and right_same_direction:
                self._explored_lanelets.append(adj_right_id)
                # Get start and end nodes of right adjacency.
                right_lanelet = self.lanelet_network.find_lanelet_by_id(adj_right_id)
                if right_lanelet.successor is not None:
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
                left_lanelet = self.lanelet_network.find_lanelet_by_id(adj_left_id)
                if left_lanelet.successor is not None:
                    successors = successors.union(set(left_lanelet.successor))
                adj_left_start = left_lanelet.center_vertices[0]
                start_node_list.append(adj_left_start)
                adj_left_end = left_lanelet.center_vertices[-1]
                end_node_list.append(adj_left_end)
                lanelets.append(left_lanelet)
                adj_left_id = left_lanelet._adj_left
                left_same_direction = left_lanelet.adj_left_same_direction

            # order lanelets from right to left
            current_lanelet = rightmost_lanelet
            ordered_lanelet_ids = [current_lanelet.lanelet_id]
            while len(lanelets) != len(ordered_lanelet_ids):
                ordered_lanelet_ids.append(current_lanelet.adj_left)
                current_lanelet = self.lanelet_network.find_lanelet_by_id(ordered_lanelet_ids[-1])

            self.lanes_dict[rightmost_lanelet.lanelet_id] = ordered_lanelet_ids
            self.edge_lengths[rightmost_lanelet.lanelet_id] = min(
                [lanelet.distance[-1] for lanelet in lanelets]
            )

            for i_lane, l_id in enumerate(ordered_lanelet_ids):
                self.lanelet_id2edge_id[l_id] = rightmost_lanelet.lanelet_id
                self.lanelet_id2edge_lane_id[l_id] = i_lane

    def _compute_node_coords(self, lanelets, index: int):
        vertices = np.array([la.center_vertices[index] for la in lanelets])
        return np.mean(vertices, axis=0)

    def _init_nodes(self):
        # creation of the start and end nodes
        # start node
        self.node_id_next = 1
        self._start_nodes = {}  # contains start nodes of each edge{edge_id: node_id}
        self._end_nodes = {}  # contains end nodes of each edge{edge_id: node_id}

        for edge_id, lanelet_ids in self.lanes_dict.items():
            self._create_node(edge_id, lanelet_ids, "from")
            self._create_node(edge_id, lanelet_ids, "to")

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
                            f"there is a problem with adjacency of the lanelet {exp}"
                        )

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
            assert len(set(node_candidates)) <= 1, "Unexpected error, please report!"
            if node_candidates:
                # assign existing node
                if node_type == "from":
                    self._start_nodes[edge_id] = node_candidates[0]
                else:
                    self._end_nodes[edge_id] = node_candidates[0]
            else:
                # create new node
                coords = self._compute_node_coords(lanelets, index=index)
                self.nodes[self.node_id_next] = Node(
                    self.node_id_next, NodeType.PRIORITY, coords, right_of_way=RightOfWay.DEFAULT
                )
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
            self.nodes[self.node_id_next] = Node(
                self.node_id_next, NodeType.PRIORITY, coords, right_of_way=RightOfWay.DEFAULT
            )
            if node_type == "from":
                self._start_nodes[edge_id] = self.node_id_next
            else:
                self._end_nodes[edge_id] = self.node_id_next

            self.node_id_next += 1

    def _stop_line_end_offset(self, lanelets: Iterable[Lanelet], end_node: Node) -> Optional[float]:
        """
        Computes the end_offset parameter, modelling the stop line for some lanelets
        :param lanelets: Lanelets composing an edge, to compute the end_offset from
        :param end_node: end node of the edge composed by lanelets.
        If the stop_lines LineMarking is SOLID or BORAD_SOLID, this node's type is set
        to ALLWAY_STOP
        :return: Optional end_offset if the given lanelets define a least one stop_line
        """
        # compute edge end_offset from composing lanelets
        projections: List[float] = []
        lengths: List[float] = []
        min_lengths: List[float] = []
        for lanelet in lanelets:
            # if no stop sign defined, or the stop sign has no lane marking, ignore it
            if not lanelet.stop_line or (
                lanelet.stop_line and lanelet.stop_line.line_marking == LineMarking.NO_MARKING
            ):
                continue
            if lanelet.stop_line.line_marking in {LineMarking.SOLID, LineMarking.BROAD_SOLID}:
                end_node.type = NodeType.ALLWAY_STOP
            center_line = LineString(lanelet.center_vertices)
            min_distances = lanelet.inner_distance
            distances = lanelet.distance
            if lanelet.stop_line.start is None or lanelet.stop_line.end is None:
                projections.append(center_line.length)
                min_lengths.append(min_distances[-1])
                lengths.append(distances[-1])
                continue
            centroid = (lanelet.stop_line.start + lanelet.stop_line.end) / 2
            proj = center_line.project(Point(centroid))
            assert 0 <= proj <= center_line.length, (
                f"Stop Line for lanelet {lanelet.lanelet_id} has to be within"
                f"it's geometry. Remove stop line for lanelet "
                f"{lanelet.lanelet_id}"
                f"or change it's start and end position to fix this."
            )
            projections.append(proj)
            lengths.append(distances[-1])
            min_lengths.append(min_distances[-1])
        if lengths and projections:
            # end offset is the mean difference to the composing lanelet's lengths
            return min(0.0, max(min(min_lengths), np.mean(lengths) - np.mean(projections)))
        return None

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
            average_width = np.sqrt(np.max(distance_array))
            return average_width

        for edge_id, lanelet_ids in self.lanes_dict.items():
            # Creation of Edge, using id as name
            start_node = self.nodes[self._start_nodes[edge_id]]
            end_node = self.nodes[self._end_nodes[edge_id]]
            lanelets = [
                self.lanelet_network.find_lanelet_by_id(lanelet_id) for lanelet_id in lanelet_ids
            ]

            # get edge type
            lanelet_types = [
                lanelet_type for lanelet in lanelets for lanelet_type in lanelet.lanelet_type
            ]
            edge_type = get_sumo_edge_type(self.edge_types, self.country_id, *lanelet_types)

            edge = Edge(
                id=edge_id,
                from_node=start_node,
                to_node=end_node,
                type_id=edge_type.id,
                spread_type=SpreadType.CENTER,
                end_offset=self._stop_line_end_offset(lanelets, end_node),
            )

            speed_limit = 0
            self.edges[edge_id] = edge
            if self.conf.overwrite_speed_limit:
                speed_limit = self.conf.overwrite_speed_limit
            # else:
            #     speed_limit = self._traffic_sign_interpreter.speed_limit(frozenset([lanelet.lanelet_id]))
            #     if speed_limit is None or np.isinf(speed_limit):
            #         speed_limit = self.conf.unrestricted_speed_limit_default

            for lanelet_id in lanelet_ids:
                shape = self._points_dict[lanelet_id]
                lanelet = self.lanelet_network.find_lanelet_by_id(lanelet_id)
                lanelet_width = calculate_lanelet_width_from_cr(lanelet)

                lane = Lane(
                    edge,
                    speed=speed_limit,
                    length=self.edge_lengths[edge_id],
                    width=lanelet_width,
                    shape=shape,
                )
                self.lanes[lane.id] = lane
                self.lane_id2lanelet_id[lane.id] = lanelet_id
                self.lanelet_id2lane_id[lanelet_id] = lane.id

        # set oncoming lanes
        for edge_id, lanelet_ids in self.lanes_dict.items():
            leftmost_lanelet = self.lanelet_network.find_lanelet_by_id(lanelet_ids[-1])
            if leftmost_lanelet.adj_left is not None:
                self.lanes[self.lanelet_id2lane_id[lanelet_ids[-1]]].setAdjacentOpposite(
                    self.lanelet_id2lane_id[leftmost_lanelet.adj_left]
                )

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
        for la in self.lanelet_network.lanelets:
            if la.successor:
                self._connections[self.lanelet_id2lane_id[la.lanelet_id]] += [
                    self.lanelet_id2lane_id[succ] for succ in la.successor
                ]

    def _filter_disallowed_vehicle_classes(
        self, max_curvature: float, lanelet_width, lanelet_id
    ) -> List[str]:
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
                (radius + lanelet_width / 2) ** 2 - (radius + self._max_vehicle_width / 2) ** 2
            )

            for veh_class, veh_length in self.conf.veh_params["length"].items():
                # only disallow vehicles longer than car (class passenger)
                if (
                    veh_length**2 > max_vehicle_length_sq
                    and veh_length > self.conf.veh_params["length"]["passenger"]
                ):
                    disallow.append(veh_class)
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

    def _encode_traffic_signs(self):
        """
        Encodes all traffic signs and writes the according changes to relevant nodes / edges
        :return:
        """
        encoder = TrafficSignEncoder(self.edge_types)
        traffic_signs: Dict[int, TrafficSign] = {
            t.traffic_sign_id: t for t in self.lanelet_network.traffic_signs
        }
        for lanelet in self.lanelet_network.lanelets:
            if not lanelet.traffic_signs:
                continue
            edge_id = self.lanelet_id2edge_id[lanelet.lanelet_id]
            if edge_id not in self.new_edges:
                self.logger.warning(
                    f"Merged Edge {edge_id} with traffic signs {lanelet.traffic_signs}. "
                    f"These Traffic signs will not be converted."
                )
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
        new_nodes: Dict[int, Node] = self.nodes.copy()
        # key is the merged node, value is a list of the nodes that form the merged node
        merged_dictionary: Dict[int, Set[Node]] = {}
        replaced_nodes: Dict[int, List[int]] = defaultdict(list)

        # compute dict with all intersecting lanelets of each lanelet based on their shapes
        intersecting_edges: Dict[int, Set[int]] = defaultdict(set)
        for pair in _find_intersecting_edges(self.lanes_dict, self.lanelet_network):
            intersecting_edges[pair[0]].add(pair[1])
            intersecting_edges[pair[1]].add(pair[0])

        # INTERSECTION BASED CLUSTERING
        # create clusters of nodes belonging to intersection elements fomr lanelet network
        def cluster_lanelets_from_intersection(
            lanelet_network, intersecting_edges
        ) -> Tuple[Dict[int, Set[Node]], Dict[int, Set[Lanelet]], Dict[int, Set[NodeType]]]:
            clusters: Dict[int, Set[Node]] = defaultdict(set)
            cluster_types: Dict[int, Set[NodeType]] = defaultdict(set)
            next_cluster_id = 0
            # crossings are additional info for a cluster
            clusters_crossing: Dict[int, Set[Lanelet]] = defaultdict(set)
            # collect intersections that are deleted afterwards
            delete_intersections = []
            for intersection in lanelet_network.intersections:
                if len(intersection.incomings) < 2:
                    # some maps model road forks using intersection elements,
                    # however sumo doesn't need a junction for this
                    continue
                cluster_instruction = self.get_cluster_instruction(
                    intersection, lanelet_network, intersecting_edges
                )
                self.logger.debug(
                    f"Clustering intersection {intersection.intersection_id} according to {cluster_instruction}"
                )
                intersect_any = False
                if cluster_instruction != ClusterInstruction.NO_CLUSTERING:
                    for incoming in intersection.incomings:
                        intersecting_lanelets = {
                            lanelet_id
                            for inc_tmp in intersection.incomings
                            for lanelet_id in inc_tmp.successors_right
                            | inc_tmp.successors_left
                            | inc_tmp.successors_straight
                            if incoming.incoming_id != inc_tmp.incoming_id
                        }
                        intersecting_lanelets -= incoming.incoming_lanelets
                        intersection_edges_others: List[Edge] = list(
                            self.edges[self.lanelet_id2edge_id[step]]
                            for step in intersecting_lanelets
                        )
                        out_lanelets_self = {
                            lanelet_id
                            for lanelet_id in incoming.successors_right
                            | incoming.successors_left
                            | incoming.successors_straight
                        }
                        out_edges_self: List[Edge] = list(
                            self.edges[self.lanelet_id2edge_id[step]] for step in out_lanelets_self
                        )
                        intersection_edges_others = list(
                            set(intersection_edges_others) - set(out_edges_self)
                        )
                        # check whether any lanelets of the intersection actually intersect,
                        # else remove the whole cluster
                        intersect = False
                        for e1 in out_edges_self:
                            for e2 in intersection_edges_others:
                                if e2.id in intersecting_edges[e1.id]:
                                    intersect = intersect_any = True
                                    # delete_intersections.append(intersection.intersection_id)
                                    break
                            if intersect:
                                break
                        if intersect is False:
                            for inc2 in intersection.incomings:
                                if inc2.left_of == incoming.incoming_id:
                                    inc2.left_of = incoming.left_of
                            del intersection._incomings[intersection._incomings.index(incoming)]

                    if intersect_any is False:
                        continue

                    if len(intersection.incomings) <= 1:
                        delete_intersections.append(intersection.intersection_id)

                    # get all edges of intersection
                    intersecting_lanelets = {
                        lanelet_id
                        for inc_tmp in intersection.incomings
                        for lanelet_id in inc_tmp.successors_right
                        | inc_tmp.successors_left
                        | inc_tmp.successors_straight
                    }
                    incoming_lanelets = {
                        lanelet_id
                        for incoming in intersection.incomings
                        for lanelet_id in incoming.incoming_lanelets
                    }
                    intersecting_lanelets -= incoming_lanelets
                    intersection_edges: List[Edge] = list(
                        self.edges[self.lanelet_id2edge_id[step]] for step in intersecting_lanelets
                    )

                    clusters[next_cluster_id] = {
                        node for e in intersection_edges for node in [e.from_node, e.to_node]
                    }
                    if cluster_instruction == ClusterInstruction.ZIPPER:
                        cluster_types[next_cluster_id].add(NodeType.ZIPPER)
                    else:
                        cluster_types[next_cluster_id].add(NodeType.PRIORITY)

                    # generate partial Crossings
                    clusters_crossing[next_cluster_id] = {
                        self.lanelet_network.find_lanelet_by_id(lanelet_id)
                        for lanelet_id in intersection.crossings
                    }
                    next_cluster_id += 1

            return clusters, clusters_crossing, cluster_types, next_cluster_id

        clusters, clusters_crossing, cluster_types, next_cluster_id = (
            cluster_lanelets_from_intersection(self.lanelet_network, intersecting_edges)
        )

        # merge overlapping clusters
        while True:
            try:
                a_id, b_id = next(
                    (a_id, b_id)
                    for a_id, a in clusters.items()
                    for b_id, b in clusters.items()
                    if a_id < b_id and a & b
                )
                clusters[a_id] |= clusters[b_id]
                del clusters[b_id]
                clusters_crossing[a_id] |= clusters_crossing[b_id]
                del clusters_crossing[b_id]
            except StopIteration:
                break

        # collect lanelet ids that ´prohibit´ other lanelets in terms of SUMO's definition
        # (i.e. that have higher priority to pass an intersection)
        # for intersection in self.lanelet_network.intersections:
        #     inc_id2incoming_element = {inc.incoming_id: inc for inc in intersection.incomings}
        #     for inc in intersection.incomings:
        #         if inc.left_of is not None:
        #             if inc.left_of in inc_id2incoming_element:
        #                 for left_of_id in inc_id2incoming_element[inc.left_of].incoming_lanelets:
        #                     self.prohibits[self.lanelet_id2lane_id[left_of_id]].extend(
        #                         [self.lanelet_id2lane_id[l]for l in inc.incoming_lanelets])
        #             else:
        #                 warnings.warn(f"ID {inc.left_of} of left_of not among incomings"
        #                               f"{list(inc_id2incoming_element.keys())} of intersection"
        #                               f"{intersection.intersection_id}"
        #                               f"-> bug in lanelet_network of CommonRoad xml file!")

        if not self.conf.highway_mode:
            # Expand merged clusters by all lanelets intersecting each other.
            # merging based on Lanelets intersecting
            explored_nodes = set()
            for current_node in self.nodes.values():
                clusters_flat = {n for cluster in clusters.values() for n in cluster}
                if current_node in explored_nodes | clusters_flat:
                    continue
                queue = [current_node]
                try:
                    current_cluster_id = next(
                        cluster_id
                        for cluster_id, cluster in clusters.items()
                        if current_node in cluster
                    )
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
                    neighbor_nodes = {
                        node
                        for edge_id in outgoings | incomings
                        for intersecting in intersecting_edges[edge_id]
                        for node in [
                            self.edges[intersecting].from_node,
                            self.edges[intersecting].to_node,
                        ]
                    }
                    neighbor_nodes -= clusters_flat
                    queue += list(neighbor_nodes)
                    current_cluster |= neighbor_nodes

                clusters[current_cluster_id] = current_cluster

            # filter clusters with 0 nodes
            clusters = {
                cluster_id: cluster for cluster_id, cluster in clusters.items() if len(cluster) > 1
            }

        # MERGE COMPUTED CLUSTERS
        for cluster_id, cluster in clusters.items():
            cluster_type = cluster_types[cluster_id]
            self.logger.info(f"Merging nodes: {[n.id for n in cluster]}")

            # create new merged node
            def merge_cluster(
                cluster: Set[Node], cluster_type: Set[NodeType] = {NodeType.PRIORITY}
            ) -> Node:
                cluster_ids = {n.id for n in cluster}
                merged_node = Node(
                    id=self.node_id_next,
                    node_type=NodeType.ZIPPER
                    if NodeType.ZIPPER in cluster_type
                    else NodeType.PRIORITY,
                    coord=np.mean([node.coord for node in cluster], axis=0),
                    right_of_way=RightOfWay.EDGE_PRIORITY,
                )
                self.node_id_next += 1
                new_nodes[merged_node.id] = merged_node
                for old_node_id in cluster_ids:
                    assert (
                        old_node_id not in replaced_nodes
                    ), f"{old_node_id} in {list(replaced_nodes.keys())}"
                    replaced_nodes[old_node_id].append(merged_node.id)
                merged_dictionary[merged_node.id] = cluster_ids
                return merged_node

            # clustered nodes at the border of a network need to be merged
            # separately, so junctions at network boundaries are converted correctly
            no_outgoing = {node for node in cluster if not node.outgoing}
            no_incoming = {node for node in cluster if not node.incoming}
            inner_cluster = cluster - no_outgoing - no_incoming
            if inner_cluster:
                merged_node = merge_cluster(inner_cluster, cluster_type)
                # Make crossing lanelets globally available
                if cluster_id in clusters_crossing:
                    self._crossings[merged_node.id] = clusters_crossing[cluster_id]
            if no_outgoing:
                merge_cluster(no_outgoing)
            if no_incoming:
                merge_cluster(no_incoming)

        replace_nodes_old = deepcopy(replaced_nodes)
        explored_nodes_all = set()
        for old_node, new_nodes_tmp in replace_nodes_old.items():
            if old_node in explored_nodes_all:
                continue

            if len(new_nodes_tmp) > 1:
                new_candidates = deepcopy(new_nodes_tmp)
                new_node = new_nodes_tmp[0]
                to_merge = set()
                explored_candidates = set()

                while new_candidates:
                    # merge with merged junction
                    new_node_tmp = new_candidates.pop()
                    if new_node_tmp in explored_candidates:
                        continue
                    explored_candidates.add(new_node_tmp)
                    to_merge |= merged_dictionary[new_node_tmp]
                    for merged_node in merged_dictionary[new_node_tmp]:
                        if len(replaced_nodes[merged_node]) > 1:
                            new_candidates = list(
                                set(new_candidates + replaced_nodes[merged_node])
                                - explored_candidates
                            )

                for node_id in explored_candidates:
                    del merged_dictionary[node_id]
                    if node_id != new_node:
                        del new_nodes[node_id]

                merged_dictionary[new_node] = to_merge
                explored_nodes_all |= to_merge
                for merged_node in to_merge:
                    replaced_nodes[merged_node] = [new_node]

        return new_nodes, merged_dictionary, replaced_nodes

    def _filter_edges(self, merged_dictionary, replaced_nodes):
        """
        Remove edges that lie inside a junction. Those will be replaced by internal edges
        :return: nothing
        """
        # new dictionary for the edges after deleting internal edges of junctions
        new_edges: Dict[int, Edge] = {}
        for edge in self.edges.values():
            if self._is_merged_edge(edge, merged_dictionary):
                continue

            edge_id = edge.id
            start_id = edge.from_node.id
            end_id = edge.to_node.id

            # update merged edges to from/to the merged node
            for new_node_id, merged_nodes in merged_dictionary.items():
                if start_id in merged_nodes:
                    edge.from_node = self.new_nodes[new_node_id]
                    break

            for new_node_id, merged_nodes in merged_dictionary.items():
                if end_id in merged_nodes:
                    edge.to_node = self.new_nodes[new_node_id]
                    break

            new_edges[edge_id] = edge

        return new_edges

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
            queue = [[via] for via in connections]  # list with edge ids to toLane
            paths = []
            # explore paths until successor not inside junction anymore
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
                    shape = np.vstack(
                        [
                            self._points_dict[self.lane_id2lanelet_id[lane_id]]
                            for lane_id in path[:-1]
                        ]
                    )
                    via = path[0:-1]
                else:
                    shape = None
                    via = None

                if self.conf.highway_mode is True:
                    keep_clear = False
                else:
                    keep_clear = True

                no_connection = False
                not_keep_clear_types = {
                    LaneletType.ACCESS_RAMP,
                    LaneletType.INTERSTATE,
                    LaneletType.EXIT_RAMP,
                }
                keep_clear_types = {LaneletType.INTERSECTION}
                for lane_id in [from_lane] + path:
                    if (
                        len(
                            not_keep_clear_types
                            & self.lanelet_network.find_lanelet_by_id(
                                self.lane_id2lanelet_id[lane_id]
                            ).lanelet_type
                        )
                        > 0
                    ):
                        keep_clear = False
                    if (
                        len(
                            keep_clear_types
                            & self.lanelet_network.find_lanelet_by_id(
                                self.lane_id2lanelet_id[lane_id]
                            ).lanelet_type
                        )
                        > 0
                    ):
                        keep_clear = True

                # don't connect on-ramps to successor -> enforces lane change instead of driving straight
                lanelet_from = self.lanelet_network.find_lanelet_by_id(
                    self.lane_id2lanelet_id[from_lane]
                )
                if (
                    LaneletType.ACCESS_RAMP in lanelet_from.lanelet_type
                    and lanelet_from.adj_left is not None
                ):
                    no_connection = True

                # if no_connection is False:
                connection = Connection(
                    from_edge=self.new_edges[int(from_lane.split("_")[0])],
                    to_edge=self.new_edges[int(path[-1].split("_")[0])],
                    from_lane=self.lanes[from_lane],
                    to_lane=self.lanes[path[-1]],
                    via_lane_id=via,
                    shape=shape,
                    keep_clear=keep_clear,
                    cont_pos=self.conf.wait_pos_internal_junctions,
                    forbidden=no_connection,
                )

                # lanes changes to access ramps are forbidden
                # lanelet = self.lanelet_network.find_lanelet_by_id(self.lane_id2lanelet_id[from_lane])
                # if lanelet.adj_right is not None and LaneletType.ACCESS_RAMP \
                #         in self.lanelet_network.find_lanelet_by_id(lanelet.adj_right).lanelet_type:
                #     connection.change_right_allowed = {}
                self._new_connections.add(connection)

    def _create_roundabouts(self, driving_direction: str = "right"):
        if driving_direction == "left":
            inner_direction = "adj_right"
        elif driving_direction == "right":
            inner_direction = "adj_left"
        else:
            raise ValueError

        def find_inner_lanelet_cycles(
            lanelet_network: LaneletNetwork, max_length: float = 180.0
        ) -> List[int]:
            lanelets = lanelet_network._lanelets
            # candidiates are lanelets without adj_{left/right}
            length_half = max_length * 0.5
            queue = [
                la
                for la, lanelet in lanelets.items()
                if not getattr(lanelet, inner_direction) and lanelet.distance[-1] < length_half
            ]
            G = nx.DiGraph()
            for la in queue:
                [G.add_edge(la, succ) for succ in lanelets[la].successor]

            cycles = list(nx.simple_cycles(G))
            for cycle in reversed(cycles):
                length = 0
                for la in cycle:
                    length += lanelets[la].inner_distance[-1]
                    if length > max_length:
                        del cycles[cycles.index(cycle)]
                        break

            return cycles

        def lanelet_cycles_2_edge_cycles(
            lanelet_cycles: List[int], lanelet_id2edge_id
        ) -> List[Roundabout]:
            roundabouts = []
            for cycle in lanelet_cycles:
                edge_cycle = list(dict.fromkeys([lanelet_id2edge_id[la] for la in cycle]))
                roundabouts.append(
                    Roundabout([self.new_edges[e] for e in edge_cycle if e in self.new_edges])
                )

            return roundabouts

        lanelet_cycles = find_inner_lanelet_cycles(self.lanelet_network)
        roundabouts = lanelet_cycles_2_edge_cycles(lanelet_cycles, self.lanelet_id2edge_id)
        self._set_roundabout_nodes_keep_clear(roundabouts, self.new_nodes)
        return roundabouts

    def _set_roundabout_nodes_keep_clear(
        self, roundabouts: List[Roundabout], nodes: Dict[int, Node]
    ):
        roundabout_nodes = set(
            itertools.chain.from_iterable(
                [e.to_node.id, e.from_node.id] for r in roundabouts for e in r.edges
            )
        )
        for node_id in roundabout_nodes:
            nodes[node_id].keep_clear = False

    def _set_prohibited_connections(self):
        """Add connections that are prohibited by a connection."""
        edges2connection = {c.from_lane.id: c for c in self._new_connections}
        edges2connection.update({via: c for c in self._new_connections for via in c.via})
        for connection in self._new_connections:
            prohibited_lanes = [
                edges2connection[p] for p in self.prohibits[connection.from_lane.id]
            ]
            prohibited_lanes.extend(
                [
                    edges2connection[p]
                    for via_lane in connection.via
                    for p in self.prohibits[via_lane]
                    if p in edges2connection
                ]
            )
            connection.prohibits = prohibited_lanes
        return True

    def _create_crossings(self):
        new_crossings = dict()
        for merged_node_id, crossing_lanelets in self._crossings.items():
            if not crossing_lanelets:
                continue
            merged_node = self.new_nodes[merged_node_id]
            adjacent_edges = {
                edge
                for edge in self.new_edges.values()
                if edge.from_node == merged_node or edge.to_node == merged_node
            }
            pedestrian_edges = {
                edge
                for edge in adjacent_edges
                if VehicleType.PEDESTRIAN in self.edge_types.types[edge.type_id].allow
            }
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
                lambda e1, e2: np.min(
                    [
                        np.linalg.norm(pt1 - pt2)
                        for lane1 in e1.lanes
                        for lane2 in e2.lanes
                        for pt1 in np.array(lane1.shape)
                        for pt2 in np.array(lane2.shape)
                    ]
                ),
            )
            crossing_lanelets = merge_lanelets(crossing_lanelets)

            crossings: List[Crossing] = []
            for edges in clusters:
                common_node: Node = reduce(
                    lambda a, b: a & b, [{edge.from_node, edge.to_node} for edge in edges]
                ).pop()
                assert common_node, "Edges in one cluster have to share a common node"
                # find vertices closest to the common node
                pts = np.array(
                    [
                        vtx
                        for edge in edges
                        for lane in edge.lanes
                        for vtx in [
                            lane.shape[-1] if edge.to_node == common_node else lane.shape[0]
                        ]
                    ]
                )
                center = np.mean(pts, axis=0)

                lanelet = crossing_lanelets[
                    int(
                        np.argmin(
                            [
                                np.min(np.linalg.norm(lanelet.center_vertices - center, axis=1))
                                for lanelet in crossing_lanelets
                            ]
                        )
                    )
                ]
                shape = lanelet.center_vertices
                c = Crossing(
                    node=merged_node,
                    edges=edges,
                    shape=shape,
                    width=float(
                        np.median(
                            np.linalg.norm(lanelet.left_vertices - lanelet.right_vertices, axis=1)
                        )
                    ),
                )
                crossings.append(c)

            new_crossings[merged_node_id] = crossings
        self._crossings = new_crossings

    def _create_traffic_lights(self):
        cr_traffic_lights: Dict[int, TrafficLight] = self.lanelet_network._traffic_lights
        node_2_traffic_light: Dict[Node, Set[TrafficLight]] = defaultdict(set)
        node_2_connections: Dict[Node, Set[Connection]] = defaultdict(set)
        light_2_connections: Dict[TrafficLight, Set[Connection]] = defaultdict(set)
        incoming_lanelet_2_intersection = self.lanelet_network.map_inc_lanelets_to_intersections
        for lanelet in self.lanelet_network.lanelets:
            if not lanelet.traffic_lights:
                continue
            lights: Set[TrafficLight] = {
                cr_traffic_lights[tl]
                for tl in lanelet.traffic_lights
                if cr_traffic_lights[tl].active
            }
            edge_id = self.lanelet_id2edge_id[lanelet.lanelet_id]
            if edge_id not in self.new_edges:
                self.logger.warning(
                    f"Edge: {edge_id} has been removed in SUMO-NET but contained a traffic light"
                )
                continue
            edge = self.new_edges[edge_id]
            node: Node = edge.to_node
            node_2_traffic_light[node] |= lights

            # maps each succeeding lanelet to the angle (in radians, [-pi, pi]) it forms with the preceding one
            # successors: Dict[Connection, float] = dict()
            #
            intersection = (
                incoming_lanelet_2_intersection[lanelet.lanelet_id]
                if lanelet.lanelet_id in incoming_lanelet_2_intersection
                else None
            )

            def calc_direction_2_connections(edge: Edge):
                connections_init = {}
                if intersection is not None:
                    incoming_elem = intersection.map_incoming_lanelets[lanelet.lanelet_id]
                    connections_init[TrafficLightDirection.STRAIGHT] = (
                        incoming_elem.successors_straight
                    )
                    connections_init[TrafficLightDirection.LEFT] = incoming_elem.successors_left
                    connections_init[TrafficLightDirection.RIGHT] = incoming_elem.successors_right
                elif len(lanelet.successor) == 1:
                    connections_init[TrafficLightDirection.STRAIGHT] = set(lanelet.successor)
                    connections_init[TrafficLightDirection.LEFT] = set(lanelet.successor)
                    connections_init[TrafficLightDirection.RIGHT] = set(lanelet.successor)
                else:
                    raise ValueError

                connections = defaultdict(set)
                for direction, init_queue in connections_init.items():
                    queue = [self.edges[self.lanelet_id2edge_id[la]] for la in init_queue]
                    visited = set()
                    while queue:
                        current = queue.pop()
                        if current in visited:
                            continue
                        visited.add(current)
                        if current.id in self.new_edges:
                            connections[direction] |= set(
                                c
                                for c in self._new_connections
                                if c.from_edge == edge and c.to_edge == current
                            )
                            continue
                        queue += current.outgoing
                return dict(connections)

            # successor_edges = succeeding_new_edges(edge)
            direction_2_connections = calc_direction_2_connections(edge)

            for light in lights:
                # try:
                direction = light.direction
                if (
                    len(lanelet.successor) == 1
                    or not light.direction
                    or light.direction == TrafficLightDirection.ALL
                ):
                    connections = set(
                        itertools.chain.from_iterable(direction_2_connections.values())
                    )
                elif intersection is not None:
                    connections = set()
                    if direction in (
                        TrafficLightDirection.RIGHT,
                        TrafficLightDirection.LEFT_RIGHT,
                        TrafficLightDirection.STRAIGHT_RIGHT,
                    ):
                        connections |= direction_2_connections[TrafficLightDirection.RIGHT]
                    if direction in (
                        TrafficLightDirection.LEFT,
                        TrafficLightDirection.LEFT_RIGHT,
                        TrafficLightDirection.LEFT_STRAIGHT,
                    ):
                        connections |= direction_2_connections[TrafficLightDirection.LEFT]
                    if direction in (
                        TrafficLightDirection.STRAIGHT,
                        TrafficLightDirection.STRAIGHT_RIGHT,
                        TrafficLightDirection.LEFT_STRAIGHT,
                    ):
                        connections |= direction_2_connections[TrafficLightDirection.STRAIGHT]
                elif len(lanelet.successor) == 1:
                    connections = set()
                else:
                    warnings.warn("Conenctions for traffic light cannot be computed")
                    node_2_traffic_light[node].remove(light)
                    continue
                node_2_connections[node] |= connections
                light_2_connections[light] |= connections
                # except KeyError:
                #     self.logger.exception(f"Unknown TrafficLightDirection: {light.direction}, "
                #                       f"could not add successors for lanelet {lanelet}")

        light_2_connections = dict(light_2_connections)
        # generate traffic lights in SUMO format
        encoder = TrafficLightEncoder(self.conf)
        for to_node, lights in node_2_traffic_light.items():
            try:
                program, connections = encoder.encode(to_node, list(lights), light_2_connections)
                self.traffic_light_signals.add_program(program)
                for connection in connections:
                    self.traffic_light_signals.add_connection(connection)
            except (RuntimeError, ValueError, TypeError):
                continue

    def _is_merged_edge(self, edge: Edge, merged_dictionary):
        """
        returns True if the edge must be removed, False otherwise
        :param edge: the edge to consider
        :return: flag remove_edge
        """
        start_node_id = edge.from_node.id
        end_node_id = edge.to_node.id

        return any(
            start_node_id in merged_nodes and end_node_id in merged_nodes
            for merged_nodes in merged_dictionary.values()
        )

    def _calculate_centroid(self, nodes: Iterable[Node]) -> np.ndarray:
        """
        Calculate the average of a given list of nodes
        :param nodes: list containing nodes
        :return: the coordinates of the average node, x and y
        """
        return np.mean([node.coord for node in nodes], axis=0)

    def auto_generate_traffic_light_system(
        self,
        lanelet_id: int,
        green_time: int = 38,
        red_time: int = 12,
        yellow_time: int = 7,
        all_red_time: int = 0,
        left_green_time: int = 6,
        crossing_min_time: int = 4,
        crossing_clearance_time: int = 5,
        time_offset: int = 0,
    ) -> bool:
        """
        Automatically generate a Traffic Light System (TLS) for all lanelets
        in the same intersection as the given lanelet_id.
        The below has been partially adapted from: https://sumo.dlr.de/docs/netconvert.html#tls_building
        :param lanelet_id: ID of lanelet in intersection to generate traffic lights for
        :param green_time: Green phase duration. [s]
        :param yellow_time: Fixed time for yellow phase durations [s]
        :param red_time: Set INT as fixed time for red phase duration at traffic
        lights that do not have a conflicting flow [s]
        :param all_red_time: Fixed time for intermediate red phase after every switch [s].
        :param left_green_time: Green phase duration for left turns. Setting this value to 0
        disables additional left-turning phases [s].
        :param crossing_min_time: Minimum time duration for pedestrian crossings [s].
        :param crossing_clearance_time: Clearance time for pedestrian crossings [s].
        :param time_offset: Offset for start time of the generated traffic lights [s].
        :return: if the conversion was successful
        """
        assert green_time > 0
        assert yellow_time > 0
        assert all_red_time >= 0
        assert left_green_time > 0
        assert crossing_min_time > 0
        assert crossing_clearance_time > 0
        assert red_time >= 0

        if not self._output_file:
            self.logger.error("Need to call create_sumo_files first")
            return False

        # did the user select an incoming lanelet to the junction?
        if lanelet_id not in self.lanelet_id2junction:
            lanelet: Lanelet = self.lanelet_network.find_lanelet_by_id(lanelet_id)
            if not lanelet:
                self.logger.warning(f"Unknown Lanelet: {lanelet_id}")
                return False
            # if the selected lanelet is not an incoming one, check the predecessors
            try:
                lanelet_id = next(
                    pred for pred in lanelet.predecessor if pred in self.lanelet_id2junction
                )
            except StopIteration:
                self.logger.warning(f"No junction found for lanelet {lanelet_id}")
                return False

        # does the lanelet already have a traffic light?
        # If so guess signals for them and copy the corresponding position
        lanelet = self.lanelet_network.find_lanelet_by_id(lanelet_id)
        guess_signals = bool(lanelet.traffic_lights)

        # auto generate the TLS with netconvert
        junction = self.lanelet_id2junction[lanelet_id]
        command = (
            f"netconvert"
            f" --sumo-net-file={self._output_file}"
            f" --output-file={self._output_file}"
            f" --tls.set={junction.id}"
            f" --tls.guess=true"
            f" --geometry.remove.keep-edges.explicit"
            f" --geometry.remove.min-length=0.0"
            f" --tls.guess-signals={'true' if guess_signals else 'false'}"
            f" --tls.group-signals=true"
            f" --tls.green.time={green_time}"
            f" --tls.red.time={red_time}"
            f" --tls.yellow.time={yellow_time}"
            f" --tls.allred.time={all_red_time}"
            f" --tls.left-green.time={left_green_time}"
            f" --tls.crossing-min.time={crossing_min_time}"
            f" --tls.crossing-clearance.time={crossing_clearance_time}"
        )
        try:
            out = subprocess.check_output(command.split(), timeout=5.0, stderr=subprocess.STDOUT)
            if "error" in str(out).lower():
                return False
        except Exception as e:
            self.logger.error(e)
            return False

        net = sumo_net_from_xml(self._output_file)
        self._update_junctions_from_net(net)
        junction = self.lanelet_id2junction[lanelet_id]

        # compute unused id value for the traffic lights
        next_cr_id = max_lanelet_network_id(self.lanelet_network) + 1

        # add generated Traffic Lights to the corresponding lanelets
        for connection in (
            conn
            for from_edges in net.connections.values()
            for from_lanes in from_edges.values()
            for to_edges in from_lanes.values()
            for conn in to_edges.values()
        ):
            # only add traffic lights the the connections at the current junction
            if connection.tls is None or connection.tls.id != str(junction.id):
                continue
            lanelet_id = self.lane_id2lanelet_id[connection.from_lane.id]
            lanelet = self.lanelet_network.find_lanelet_by_id(lanelet_id)
            traffic_light = TrafficLight(
                traffic_light_id=next_cr_id,
                traffic_light_cycle=TrafficLightCycle(
                    [
                        TrafficLightCycleElement(
                            state=traffic_light_states_SUMO2CR[phase.state[connection.tl_link]],
                            duration=round(phase.duration / self.conf.dt),
                        )
                        for phase in connection.tls.phases
                    ],
                    time_offset=time_offset / self.conf.dt,
                ),
                direction=directions_SUMO2CR[connection.direction],
                position=lanelet.right_vertices[-1],
            )
            next_cr_id += 1
            assert self.lanelet_network.add_traffic_light(
                traffic_light, {lanelet_id}
            ), f"Could not add traffic light to lanelet: {lanelet_id}"

        return True

    def write_intermediate_files(self, output_path: str) -> Tuple[str, ...]:
        """
        Function for writing the edges and nodes files in xml format
        :param output_path: the relative path of the output
        :return: None
        """

        return (
            self._write_nodes_file(output_path),
            self._write_edges_file(output_path),
            self._write_connections_file(output_path),
            self._write_traffic_file(output_path),
            self._write_edge_type_file(output_path),
        )

    def _write_nodes_file(self, output_path: str) -> str:
        """
        Functio for writing the nodes file
        :param output_path: path for the file
        :return: nothing
        """
        file_path = os.path.join(os.path.dirname(output_path), f"{self.conf.scenario_name}.nod.xml")
        with open(file_path, "w+") as output_file:
            sumolib.writeXMLHeader(output_file, "CommonRoad Scenario Designer")
            nodes = etree.Element("nodes")

            for node in self.new_nodes.values():
                nodes.append(etree.fromstring(node.to_xml()))

            # pretty print & write the generated xml
            output_file.write(
                str(etree.tostring(nodes, pretty_print=True, encoding="utf-8"), encoding="utf-8")
            )

        self._nodes_file = file_path
        return file_path

    def _write_edges_file(self, output_path: str) -> str:
        """
        Function for writing the edges file
        :param output_path: path for the file
        :return: nothing
        """
        file_path = os.path.join(os.path.dirname(output_path), f"{self.conf.scenario_name}.edg.xml")
        with open(file_path, "w+") as output_file:
            sumolib.writeXMLHeader(output_file, "CommonRoad Scenario Designer")
            edges = etree.Element("edges")
            for edge in self.new_edges.values():
                edges.append(etree.fromstring(edge.to_xml()))

            for roundabout in self.roundabouts:
                edges.append(etree.fromstring(roundabout.to_xml()))

            # pretty print & write the generated xml
            output_file.write(
                str(etree.tostring(edges, pretty_print=True, encoding="utf-8"), encoding="utf-8")
            )

        self._edges_file = file_path
        return file_path

    def _write_connections_file(self, output_path: str) -> str:
        """
        Function for writing the connections file
        :param output_path: path for the file
        :return: nothing
        """
        file_path = os.path.join(os.path.dirname(output_path), f"{self.conf.scenario_name}.con.xml")
        with open(file_path, "w+") as output_file:
            sumolib.writeXMLHeader(output_file, "CommonRoad Scenario Designer")
            connections = etree.Element("connections")
            for connection in self._new_connections:
                connections.append(etree.fromstring(connection.to_xml()))
                [connections.append(etree.fromstring(p)) for p in connection.get_prohibition_xmls()]
            for crossings in self._crossings.values():
                for crossing in crossings:
                    connections.append(etree.fromstring(crossing.to_xml()))

            # pretty print & write the generated xml
            output_file.write(
                str(
                    etree.tostring(connections, pretty_print=True, encoding="utf-8"),
                    encoding="utf-8",
                ).replace("&gt;", ">")
            )

        self._connections_file = file_path
        return file_path

    def _write_traffic_file(self, output_path: str) -> str:
        """
        Writes the tll.net.xml file to disk
        :param output_path: path for the file
        """
        file_path = os.path.join(os.path.dirname(output_path), f"{self.conf.scenario_name}.tll.xml")
        with open(file_path, "w+") as f:
            sumolib.writeXMLHeader(f, "CommonRoad Scenario Designer")
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
            sumolib.writeXMLHeader(f, "CommonRoad Scenario Designer")
            types = etree.fromstring(self.edge_types.to_xml())
            f.write(
                str(etree.tostring(types, pretty_print=True, encoding="utf-8"), encoding="utf-8")
            )
        self._type_file = file_path
        return file_path

    def merge_intermediate_files(
        self,
        output_path: str,
        cleanup: bool,
        nodes_path: str,
        edges_path: str,
        connections_path: str,
        traffic_path: str,
        type_path: str,
    ) -> bool:
        """
        Function that merges the edges and nodes files into one using netconvert
        :param output_path
        :param cleanup: deletes temporary input files after creating net file (only deactivate for debugging)
        :param connections_path:
        :param nodes_path:
        :param edges_path:
        :param traffic_path:
        :param type_path:
        :param output_path: the relative path of the output
        :return: bool: returns False if conversion fails
        """

        # The header of the xml files must be removed
        to_remove = ["options", "xml"]
        for path in [nodes_path, edges_path, connections_path, traffic_path]:
            # Removing header in file
            with open(path, "r") as file:
                lines = file.readlines()
            with open(path, "w") as file:
                for line in lines:
                    if not any(word in line for word in to_remove):
                        file.write(line)

        self._output_file = str(output_path)
        # Calling of Netconvert
        command = (
            f"{os.environ['SUMO_HOME']}/bin/netconvert "
            f" --no-turnarounds=true"
            f" --junctions.internal-link-detail=20"
            f" --geometry.avoid-overlap=true"
            f" --geometry.remove.keep-edges.explicit=true"
            f" --geometry.remove.min-length=0.0"
            f" --tls.guess-signals=true"
            f" --tls.group-signals=true"
            f" --tls.green.time={50}"
            f" --tls.red.time={50}"
            f" --tls.yellow.time={10}"
            f" --tls.allred.time={50}"
            f" --tls.left-green.time={50}"
            f" --tls.crossing-min.time={50}"
            f" --tls.crossing-clearance.time={50}"
            f" --offset.disable-normalization=true"
            f" --node-files={nodes_path}"
            f" --edge-files={edges_path}"
            f" --connection-files={connections_path}"
            f" --tllogic-files={traffic_path}"
            f" --type-files={type_path}"
            f" --output-file={output_path}"
            f" --seed={self.conf.random_seed_trip_generation}"
        )
        success = True
        try:
            _ = subprocess.check_output(command.split(), timeout=5.0)
            # update lengths
            update_edge_lengths(self._output_file)
            net = sumo_net_from_xml(self._output_file)
            self._update_junctions_from_net(net)

            # if update_internal_ids:
            #     self._update_internal_IDs_from_net_file(self._output_file)

        except FileNotFoundError as e:
            if "netconvert" in e.filename:
                warnings.warn("Is netconvert installed and added to PATH?")
            success = False
        except ScenarioException:
            raise
        except Exception as e:
            self.logger.exception(e)
            success = False

        if cleanup and success:
            for path in [nodes_path, edges_path, connections_path, traffic_path]:
                os.remove(path)

        return success

    def _update_internal_IDs_from_net_file(self, net_file_path: str):
        with open(net_file_path, "r") as f:
            root = ET.parse(f)

        def grouped_list(list, criterion):
            return groupby(sorted(list, key=criterion), key=criterion)

        original_connection_map = {
            str(from_edge): {
                str(from_lane.split("_")[-1]): {
                    str(to_edge): {
                        str(to_lane.split("_")[-1]): [
                            connection.via for connection in to_lane_connections
                        ]
                        for to_lane, to_lane_connections in grouped_list(
                            to_edge_connections, lambda c: c.to_lane.id
                        )
                    }
                    for to_edge, to_edge_connections in grouped_list(
                        from_lane_connections, lambda c: c.to_edge.id
                    )
                }
                for from_lane, from_lane_connections in grouped_list(
                    from_edge_connections, lambda c: c.from_lane.id
                )
            }
            for from_edge, from_edge_connections in grouped_list(
                self._new_connections, lambda c: c.from_edge.id
            )
        }

        available_lane_ids = set()

        for connection_xml in root.findall("connection"):
            from_edge_id = connection_xml.get("from")
            to_edge_id = connection_xml.get("to")

            from_lane_id = connection_xml.get("fromLane")
            to_lane_id = connection_xml.get("toLane")

            # Add seen lane ids to the available set
            available_lane_ids |= {f"{from_edge_id}_{from_lane_id}", f"{to_edge_id}_{to_lane_id}"}

            # Skip the connections from or to internal edges
            if from_edge_id.startswith(":") or to_edge_id.startswith(":"):
                continue

            # Skip the normal connection
            new_internal_connection_id = connection_xml.get("via")
            if not new_internal_connection_id or not new_internal_connection_id.startswith(":"):
                continue

            # if new_internal_connection_ID.contains(' '):
            #     raise ScenarioException("There is no lanelet between intersections/junctions,
            #     which causes that these intersections must be merged in SUMO,
            #     therefore multiple internal edges would be in this merged intersection, which is not supported!")

            new_internal_connection_id_split = new_internal_connection_id.split("_")
            new_internal_edge_id = (
                f"{new_internal_connection_id_split[0]}_{new_internal_connection_id_split[1]}"
            )
            new_internal_lane_id = int(new_internal_connection_id_split[2])

            try:
                original_internal_connection_ids = original_connection_map[from_edge_id][
                    from_lane_id
                ][to_edge_id][to_lane_id]
            except KeyError as invalid_key:
                raise ScenarioException(
                    f"Inconsistent scenario, there is no connection between "
                    f"from: {from_edge_id}_{from_lane_id}, to: {to_edge_id}_{to_lane_id}, {invalid_key}"
                )

            if len(original_internal_connection_ids) > 1:
                raise RuntimeError(
                    f"The connection is ambiguous between from {from_edge_id}_{from_lane_id}, "
                    f"to {to_edge_id}_{to_lane_id}"
                )
            original_internal_connection_ids = original_internal_connection_ids[0]

            # If there is no internal connection, continue
            if original_internal_connection_ids is None:
                continue

            for original_internal_connection_ID in original_internal_connection_ids:
                original_lanelet_ID = self.lane_id2lanelet_id[original_internal_connection_ID]

                # Update the dictionaries
                if new_internal_connection_id in self.lane_id2lanelet_id:
                    if not isinstance(self.lane_id2lanelet_id[new_internal_connection_id], list):
                        self.lane_id2lanelet_id[new_internal_connection_id] = [
                            self.lane_id2lanelet_id[new_internal_connection_id]
                        ]
                    self.lane_id2lanelet_id[new_internal_connection_id].append(original_lanelet_ID)
                else:
                    self.lane_id2lanelet_id[new_internal_connection_id] = original_lanelet_ID

                self.lanelet_id2edge_id[original_lanelet_ID] = new_internal_edge_id
                self.lanelet_id2edge_lane_id[original_lanelet_ID] = new_internal_lane_id
                self.lanelet_id2lane_id[original_lanelet_ID] = new_internal_connection_id

        # available_lanelet_ids = {self.lane_id2lanelet_id[available_lane_id] for available_lane_id in
        # available_lane_ids if available_lane_id in self.lane_id2lanelet_id}

        for lanelet in self.lanelet_network.lanelets:
            lanelet_id = lanelet.lanelet_id
            lane_id = self.lanelet_id2lane_id[lanelet_id]
            if lane_id not in available_lane_ids:
                del self.lanelet_id2edge_id[lanelet_id]
                del self.lanelet_id2edge_lane_id[lanelet_id]
                del self.lanelet_id2lane_id[lanelet_id]

    def _update_junctions_from_net(self, net: Net):
        # parse junctions from .net.xml
        for junction in net.junctions.values():
            if junction.inc_lanes is None:
                continue
            for lane in junction.inc_lanes:
                # skip internal lanes
                if lane.id not in self.lane_id2lanelet_id:
                    continue
                self.lanelet_id2junction[self.lane_id2lanelet_id[lane.id]] = junction

    def create_sumo_files(
        self, output_folder: str, traffic_from_trajectories=False, cleanup_tmp_files=True
    ) -> bool:
        """
        Convert the CommonRoad scenario to a net.xml file, specified by the absolute path output_file and create
        all SUMO files required for the traffic simulation.
        :param output_folder of the returned SUMO files
        :param traffic_from_trajectories: if True, create route files based on trajectories from CommonRoad scenario;
            if False, create traffic randomly using SUMO's randomTrips script
        :param cleanup_tmp_files: clean up temporary files created during the .net conversion, useful for debugging
        :return returns whether conversion was successful
        """
        output_path = os.path.join(output_folder, self.conf.scenario_name + ".net.xml")
        self.logger.info("Converting to SUMO Map")
        self.logger.info(output_folder)
        self.logger.info(self.conf.scenario_name)
        self._convert_map()

        self.logger.info("Merging Intermediate Files")
        intermediary_files = self.write_intermediate_files(output_path)
        conversion_possible = self.merge_intermediate_files(
            output_path, cleanup_tmp_files, *intermediary_files
        )
        if not conversion_possible:
            self.logger.error("Error converting map, see above for details")
            return False

        self.logger.info("Generating Traffic Routes")
        if traffic_from_trajectories is True:
            return self._create_routes_from_trajectories(self.initial_scenario, output_folder)
        else:
            return self._create_random_routes(output_path)

    def _create_routes_from_trajectories(self, scenario: Scenario, output_folder: str) -> bool:
        """
        Convert the Commonroad trajectories to SUMO routes. Next to the route files add file will be created as well
        :param scenario: the scenario to be converted
        :param output_folder: path to the output folder
        :return returns whether conversion was successful
        """
        scenario_name = self.conf.scenario_name
        net_file = os.path.join(output_folder, scenario_name + ".net.xml")

        rou_files = self._create_rou_file_from_trajectories(scenario, output_folder)

        self.sumo_cfg_file = self.generate_cfg_file(
            scenario_name, net_file, rou_files, output_folder
        )
        return True

    def _create_random_routes(
        self, net_file: str, scenario_name: str = None, return_files=True
    ) -> bool:
        """
        Automatically generates traffic routes from the given .net.xml file

        :param net_file: Path of the SUMO .net.xml file
        :return bool: If the conversion was successful
        """
        if len(self.conf.ego_ids) > self.conf.n_ego_vehicles:
            self.logger.error(
                "total number of given ego_vehicles must be <= n_ego_vehicles, but {}not<={}".format(
                    len(self.conf.ego_ids), self.conf.n_ego_vehicles
                )
            )
            return False

        if self.conf.n_ego_vehicles > self.conf.n_vehicles_max:
            self.logger.error(
                "Number of ego vehicles needs to be <= than the total number of vehicles."
                " n_ego_vehicles: {} > n_vehicles_max: {}".format(
                    self.conf.n_ego_vehicles, self.conf.n_vehicles_max
                )
            )
            return False

        if scenario_name is None:
            scenario_name = self.conf.scenario_name
        out_folder = os.path.dirname(net_file)

        self._additional_file = self._generate_add_file(scenario_name, out_folder)
        rou_files = self._generate_rou_file(net_file, scenario_name, out_folder)

        self.sumo_cfg_file = self.generate_cfg_file(scenario_name, net_file, rou_files, out_folder)
        if return_files is False:
            return True
        else:
            return rou_files, self._additional_file, self.sumo_cfg_file

    def _convert_to_add_file(self, scenario: Scenario, xml_root, domTree) -> str:
        """
        During converting the Commonroad trajectories to SUMO routes add file is required for SUMO.
        :param scenario: the scenario to be converted
        :param output_folder: path to the output folder
        :return: the path of the created add file
        """

        # config parameters for easy access
        vehicle_params = self.conf.veh_params
        driving_params = self.conf.driving_params

        def get_grouped_obstacles(obstacle_list):
            return {
                obstacle_id: list(obstacles)
                for obstacle_id, obstacles in groupby(
                    sorted(obstacle_list, key=lambda obstacle: obstacle.obstacle_type.value),
                    key=lambda obstacle: obstacle.obstacle_type,
                )
            }

        num_all_obstacles = len(scenario.obstacles)
        grouped_obstacles = {
            ObstacleRole.STATIC: get_grouped_obstacles(scenario.static_obstacles),
            ObstacleRole.DYNAMIC: get_grouped_obstacles(scenario.dynamic_obstacles),
        }

        for veh_role, type_grouped_obstacles in grouped_obstacles.items():
            for veh_type, obstacle_list in type_grouped_obstacles.items():
                try:
                    sumo_veh_type = VEHICLE_TYPE_CR2SUMO[veh_type]
                    if veh_role == ObstacleRole.STATIC:
                        sumo_veh_type_name = veh_type.value + "_static"
                    else:
                        sumo_veh_type_name = veh_type.value + "_dynamic"
                except KeyError:
                    self.logger.warning(f"{veh_type} could not be converted to SUMO")
                    continue
                vType_node = domTree.createElement("vType")
                xml_root.appendChild(vType_node)
                vType_node.setAttribute("id", sumo_veh_type_name)
                vType_node.setAttribute("guiShape", sumo_veh_type.value)
                vType_node.setAttribute("vClass", sumo_veh_type.value)
                vType_node.setAttribute("probability", str(len(obstacle_list) / num_all_obstacles))

                for att_name, setting in vehicle_params.items():
                    att_value = setting[veh_type]
                    if type(att_value) is Interval:
                        att_value = str(0.5 * (att_value.start + att_value.end))
                    else:
                        att_value = str(att_value)
                    vType_node.setAttribute(att_name, att_value)
                for att_name, att_value in driving_params.items():
                    if type(att_value) is Interval:
                        att_value = 0.5 * (att_value.start + att_value.end)
                    vType_node.setAttribute(att_name, str("{0:.2f}".format(att_value)))
                if veh_role == ObstacleRole.STATIC:
                    vType_node.setAttribute("maxSpeed", str(f"{sys.float_info.min}"))

    def _generate_add_file(self, scenario_name: str, output_folder: str) -> str:
        """
        Generate additional file for sumo scenario to define attributes of different vehicle types.

        :param output_folder: the generated add file will be saved here
        :return: additional file
        """

        def add_driving_params(vType_node, driving_params):
            for att_name, value_interval in driving_params.items():
                if isinstance(value_interval, Interval):
                    att_value = np.random.uniform(value_interval.start, value_interval.end, 1)[0]
                elif isinstance(value_interval, (int, float)):
                    att_value = value_interval
                else:
                    raise ValueError(
                        f"Unknown vehicle parameter value/interval '{value_interval}'."
                    )

                vType_node.setAttribute(att_name, str("{0:.2f}".format(att_value)))

        add_file = os.path.join(output_folder, scenario_name + ".add.xml")

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
                        att_value = np.random.uniform(att_value.start, att_value.end, 1)[0]
                        att_value = str("{0:.2f}".format(att_value))
                    else:
                        att_value = str(att_value)
                    vType_node.setAttribute(att_name, att_value)

                add_driving_params(vType_node, driving_params)
                vType_dist_node.appendChild(vType_node)

        with open(add_file, "w") as f:
            domTree.documentElement.writexml(f, addindent="\t", newl="\n")

        self.logger.info("Additional file written to {}".format(add_file))
        return add_file

    def _create_rou_file_from_trajectories(
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

        route_matcher = LaneletRouteMatcher(scenario, VehicleTypeParam.FORD_ESCORT)

        @lru_cache(512)
        def get_ccosy(lane_id: str):
            return create_coordinate_system_from_polyline(self.lanes[lane_id].shape)

        def relative_orientation(from_angle1_in_rad, to_angle2_in_rad):
            phi = (to_angle2_in_rad - from_angle1_in_rad) % (2 * np.pi)
            if phi > np.pi:
                phi -= 2 * np.pi

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

        def sorted_lanelet_ids(
            lanelet_ids: List[int], orientation: float, position: np.ndarray, scenario: Scenario
        ) -> List[int]:
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
                    list(map(get_lanelet_relative_orientation, lanelet_id_list))
                )
                sorted_indices = np.argsort(orientation_differences)
                return list(lanelet_id_list[sorted_indices])

        def create_coordinate_system_from_polyline(
            polyline,
        ) -> CurvilinearCoordinateSystem:
            def compute_polyline_length(polyline: np.ndarray) -> float:
                """
                Computes the path length s of a given polyline
                :param polyline: The polyline
                :return: The path length of the polyline
                """
                assert (
                    isinstance(polyline, np.ndarray)
                    and polyline.ndim == 2
                    and len(polyline[:, 0]) > 2
                ), "Polyline malformed for path length computation p={}".format(polyline)

                distance_between_points = np.diff(polyline, axis=0)
                # noinspection PyTypeChecker
                return np.sum(np.sqrt(np.sum(distance_between_points**2, axis=1)))

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

            return CurvilinearCoordinateSystem(polyline, CLCSParams())

        def get_long_dist(ccosy, position):
            try:
                rel_pos_to_domain = 0
                long_dist, lat_dist = ccosy.convert_to_curvilinear_coords(position[0], position[1])
                return long_dist, rel_pos_to_domain
            except ValueError:
                eps = 0.1
                curvi_coords_of_projection_domain = np.array(ccosy.curvilinear_projection_domain())

                longitudinal_min, normal_min = (
                    np.min(curvi_coords_of_projection_domain, axis=0) + eps
                )
                longitudinal_max, normal_max = (
                    np.max(curvi_coords_of_projection_domain, axis=0) - eps
                )
                normal_center = (normal_min + normal_max) / 2

                bounding_points = np.array(
                    [
                        ccosy.convert_to_cartesian_coords(longitudinal_min, normal_center),
                        ccosy.convert_to_cartesian_coords(longitudinal_max, normal_center),
                    ]
                )
                rel_positions = position - np.array(
                    [bounding_point for bounding_point in bounding_points]
                )
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
            possible_lanelet_ids = scenario.lanelet_network.find_lanelet_by_position(
                [state.position]
            )[0]

            if len(possible_lanelet_ids) == 0:
                possible_lanelet_ids = scenario.lanelet_network.find_lanelet_by_shape(
                    obstacle.occupancy_at_time(state.time_step).shape
                )

            sorted_lanelet_id_list = sorted_lanelet_ids(
                possible_lanelet_ids, state.orientation, state.position, scenario
            )
            if len(sorted_lanelet_id_list) == 0:
                return None
            return sorted_lanelet_id_list[0]

        def get_position_in_lane(lanelet_id, position):
            # If the lanelet is merged in one SUMO lane, the lanelets must be merged too
            lane_id = self.lanelet_id2lane_id[lanelet_id]
            # In SUMO the starting point of the vehicle is used as position, not the center
            depart_pos, _ = get_long_dist(get_ccosy(lane_id), position)
            depart_pos += sumo_veh_length_center

            return depart_pos

        grouped_obstacles = {
            k: list(g)
            for k, g in groupby(
                sorted(scenario.obstacles, key=lambda obstacle: obstacle.obstacle_type.value),
                key=lambda obstacle: obstacle.obstacle_type,
            )
        }

        # filenames
        route_files: Dict[str, str] = {
            "vehicle": os.path.join(out_folder, self.conf.scenario_name + ".vehicles.rou.xml"),
            "pedestrian": os.path.join(
                out_folder, self.conf.scenario_name + ".pedestrians.rou.xml"
            ),
        }

        for route_type, route_file in route_files.items():

            def flatten(la):
                return [item for sublist in la for item in sublist]

            route_obstacles = flatten(
                [
                    obstacles
                    for obstacle_type, obstacles in grouped_obstacles.items()
                    if VEHICLE_NODE_TYPE_CR2SUMO[obstacle_type] == route_type
                ]
            )

            domTree = minidom.Document()
            routes_node = domTree.createElement("routes")
            domTree.appendChild(routes_node)
            if route_type == "vehicle":
                self._convert_to_add_file(scenario, routes_node, domTree)
            vType_dist_node = domTree.createElement("vTypeDistribution")
            vType_dist_node.setAttribute("id", "DEFAULT_VEHTYPE")

            for obstacle in route_obstacles:
                vehicle_node = domTree.createElement("vehicle")

                vehicle_node.setAttribute("id", str(obstacle.obstacle_id))
                sumo_veh_length_center = self.conf.veh_params["length"][obstacle.obstacle_type] / 2

                if obstacle.obstacle_role == ObstacleRole.STATIC:
                    vehicle_node.setAttribute("depart", str(scenario.dt))
                    vehicle_node.setAttribute("departSpeed", str(0))
                    vehicle_node.setAttribute("type", f"{obstacle.obstacle_type.value}_static")

                    starting_lanelet_id = find_lanelet_id(obstacle.initial_state)
                    if starting_lanelet_id not in self.lanelet_id2edge_lane_id:
                        self.logger.warning(
                            f"The used starting lanelet {starting_lanelet_id} of the static obstacle "
                            f"{obstacle.obstacle_id} was not converted into the SUMO map,"
                            f"the obstacle will be skipped!"
                        )
                        continue
                    depart_lane = self.lanelet_id2edge_lane_id[starting_lanelet_id]
                    vehicle_node.setAttribute("departLane", str(depart_lane))

                    depart_pos = get_position_in_lane(
                        starting_lanelet_id, obstacle.initial_state.position
                    )
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
                            f"has no trajectory"
                        )

                    vehicle_node.setAttribute(
                        "depart", str(obstacle.prediction.initial_time_step * scenario.dt)
                    )
                    vehicle_node.setAttribute(
                        "departSpeed",
                        str(
                            min(
                                obstacle.initial_state.velocity,
                                self.conf.veh_params["maxSpeed"][obstacle.obstacle_type],
                            )
                        ),
                    )
                    vehicle_node.setAttribute("type", f"{obstacle.obstacle_type.value}_dynamic")

                    if not isinstance(obstacle.prediction, TrajectoryPrediction):
                        raise ScenarioException(
                            f"Only scenario with TrajectoryPrediction is supported for rou file generation, "
                            f"the current obstacle was {type(obstacle.prediction)}"
                        )

                    try:
                        lanelet_ids, _ = route_matcher.find_lanelets_by_trajectory(
                            obstacle.prediction.trajectory,
                            exclude_oncoming_lanes=True,
                            required_properties=[],
                        )
                    except ValueError:
                        self.logger.warning(
                            f"Could not match route for obstacle {obstacle.obstacle_id}!"
                        )
                        continue

                    # Add one successor to force the obstacle to leave the lanelet
                    last_lanelet = scenario.lanelet_network.find_lanelet_by_id(lanelet_ids[-1])
                    if len(last_lanelet.successor) > 0:
                        lanelet_ids.append(last_lanelet.successor[0])

                    # Add successors until not ending in internal edge
                    while lanelet_ids[-1] in self.lanelet_id2edge_id and str(
                        self.lanelet_id2edge_id[lanelet_ids[-1]]
                    ).startswith(":"):
                        last_lanelet = scenario.lanelet_network.find_lanelet_by_id(lanelet_ids[-1])
                        lanelet_ids.append(last_lanelet.successor[0])

                    # Remove all the not converted lanelets
                    lanelet_ids_tmp = [
                        lanelet_id
                        for lanelet_id in lanelet_ids
                        if lanelet_id in self.lanelet_id2edge_id
                    ]

                    if len(lanelet_ids_tmp) == 0:
                        self.logger.warning(
                            f"None of the used lanelets of the vehicle {obstacle.obstacle_id} has been converted,"
                            f"original lanelet IDs was: {lanelet_ids}, the vehicle will be skipped"
                        )
                        continue
                    lanelet_ids = lanelet_ids_tmp

                    starting_lanelet_id = lanelet_ids[0]
                    depart_lane = self.lanelet_id2edge_lane_id[starting_lanelet_id]
                    vehicle_node.setAttribute("departLane", str(depart_lane))

                    depart_pos = get_position_in_lane(
                        starting_lanelet_id, obstacle.initial_state.position
                    )
                    vehicle_node.setAttribute("departPos", str(depart_pos))

                    vehicle_route_node = domTree.createElement("route")

                    edge_ids = [self.lanelet_id2edge_id[lanelet_id] for lanelet_id in lanelet_ids]
                    # When junctions are created, the connecting edges in those junctions are removed.
                    # To make sure, we do not reference removed edges in the resulting route, we collect only edges,
                    # which are present after the internal edges were removed.
                    filtered_edges = [edge_id for edge_id in edge_ids if edge_id in self.new_edges]
                    # remove consecutive duplicates e.g. [26, 26, 28, 27, 26] becomes [26, 28, 27, 26]
                    deduplicated_filtered_edges = [x[0] for x in groupby(filtered_edges)]

                    deduplicated_filtered_edges_str = [
                        str(edge_id) for edge_id in deduplicated_filtered_edges
                    ]
                    vehicle_route_node.setAttribute(
                        "edges", " ".join(deduplicated_filtered_edges_str)
                    )
                    vehicle_node.appendChild(vehicle_route_node)

                    routes_node.appendChild(vehicle_node)
                else:
                    self.logger.warning(
                        "Obstacle %s in scenario %s has unknown role %s, " "skipping this obstacle",
                        obstacle.obstacle_id,
                        scenario.scenario_id,
                        obstacle.obstacle_role,
                    )

            with open(route_file, "w") as f:
                domTree.documentElement.writexml(f, addindent="\t", newl="\n")

            self.logger.info("Route file written to {}".format(route_file))

        return route_files

    def get_cluster_instruction(
        self,
        intersection: Intersection,
        lanelet_network: LaneletNetwork,
        intersection_edges: Dict[int, List[int]],
    ):
        def get_all_adj(lanelet_id):
            adjacent_lanelets = set()
            if lanelet_network._lanelets[lanelet_id].adj_left is not None:
                adjacent_lanelets.add(lanelet_network._lanelets[lanelet_id].adj_left)
            if lanelet_network._lanelets[lanelet_id].adj_right is not None:
                adjacent_lanelets.add(lanelet_network._lanelets[lanelet_id].adj_right)

            return adjacent_lanelets

        def get_all_successors(lanelets: Set[int]) -> Set[int]:
            return set(
                itertools.chain.from_iterable(
                    set(lanelet_network.find_lanelet_by_id(la).successor) for la in lanelets
                )
            )

        if self.conf.highway_mode:
            zipper_return = ClusterInstruction.ZIPPER
        else:
            zipper_return = ClusterInstruction.CLUSTERING

        # check whether all successors are laterally adjacent at least successors
        # from two different incomings are adjacent-> choose zipper type
        successor_criterion = True
        s_types = ["successors_straight", "successors_left", "successors_right"]
        all_successors = set(
            itertools.chain.from_iterable(
                getattr(inc, s_typ) for inc in intersection.incomings for s_typ in s_types
            )
        )
        for s in all_successors:
            if not get_all_adj(s) & all_successors:
                successor_criterion = False
                break

        adj_other = False
        inc2successors = {
            inc.incoming_id: set(
                itertools.chain.from_iterable(getattr(inc, s_typ) for s_typ in s_types)
            )
            for inc in intersection.incomings
        }
        for inc_id, succ_tmp in inc2successors.items():
            for s in succ_tmp:
                adj = get_all_adj(s)
                for inc_id_other, succ_tmp2 in inc2successors.items():
                    if inc_id_other == inc_id:
                        continue
                    if adj & succ_tmp2:
                        adj_other = True
                        break

        if successor_criterion is True and adj_other is True:
            return zipper_return

        lanelet_2_inc = intersection.map_incoming_lanelets
        inc_lanelets = set(lanelet_2_inc.keys())
        inc_2_incoming_lanelets = defaultdict(list)
        for lanelet, incoming in lanelet_2_inc.items():
            inc_2_incoming_lanelets[incoming].append(lanelet)

        # check whether in all incoming at least one lanelet is adjacent to another incoming
        adjacency_criterion = True  # is falsified if at least one incoming doesn't fulfil criterion
        # check whether two incomings are merging
        zipper_criterion = False  # only needs to occur once
        for inc, inc_lanelets in inc_2_incoming_lanelets.items():
            is_adj_with_other_incoming = False
            for l_id in inc_lanelets:
                is_adj_with_other_incoming = False
                other_inc_lanelets = set(
                    itertools.chain.from_iterable(
                        [
                            incoming_lanelets
                            for inc_other, incoming_lanelets in inc_2_incoming_lanelets.items()
                            if inc != inc_other
                        ]
                    )
                )
                if set(get_all_adj(l_id)) & other_inc_lanelets:
                    is_adj_with_other_incoming = True
                if set(lanelet_network.find_lanelet_by_id(l_id).successor) & get_all_successors(
                    other_inc_lanelets
                ):
                    zipper_criterion = True

            if is_adj_with_other_incoming is False:
                adjacency_criterion = False

        # zipper with > 2 edges undefined
        if len(intersection.incomings) == 2:
            zipper_criterion = False

        if adjacency_criterion is True:
            if zipper_criterion is True:
                return zipper_return
            else:
                return ClusterInstruction.NO_CLUSTERING

        # check whether lanelets of intersection are even intersecting
        non_intersecting_criterion = True
        succ_edges = {self.lanelet_id2edge_id[s] for s in all_successors}
        for edge_id in succ_edges:
            if edge_id in intersection_edges:
                intersecting_edges_tmp = set(intersection_edges[edge_id]) & succ_edges
                for edge_tmp in intersecting_edges_tmp:
                    # intersections are not counted, if they occur between forking edges
                    if self.edges[edge_id].from_node.id != self.edges[edge_tmp].from_node.id:
                        non_intersecting_criterion = False
                        break

        if non_intersecting_criterion is True:
            return ClusterInstruction.NO_CLUSTERING

        return ClusterInstruction.CLUSTERING

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
            period = 1 / (self.conf.max_veh_per_km * (total_lane_length / 1000) * self.conf.dt)
            self.logger.info(
                "SUMO traffic generation: traffic frequency is defined "
                "based on the total lane length of the road network."
            )
        elif self.conf.veh_per_second is not None:
            # vehicles per second
            period = 1 / (self.conf.veh_per_second * self.conf.dt)
            self.logger.info(
                "SUMO traffic generation: the total_lane_length of the road network is not available. "
                "Traffic frequency is defined based on equidistant depature time."
            )
        else:
            period = 0.5
            self.logger.info(
                "SUMO traffic generation: neither total_lane_length nor veh_per_second is defined. "
                "For each second there are two vehicles generated."
            )

        # step_per_departure = ((conf.departure_interval_vehicles.end -
        # conf.departure_interval_vehicles.start) / n_vehicles_max)

        # filenames
        route_files: Dict[str, str] = {
            "vehicle": os.path.join(out_folder, scenario_name + ".vehicles.rou.xml"),
        }
        trip_files: Dict[str, str] = {
            "vehicle": os.path.join(out_folder, scenario_name + ".vehicles.trips.xml"),
        }

        if self.conf.veh_distribution[ObstacleType.PEDESTRIAN] > 0:
            route_files["pedestrian"] = os.path.join(
                out_folder, scenario_name + ".pedestrians.rou.xml"
            )
            trip_files["pedestrian"] = os.path.join(
                out_folder, scenario_name + ".pedestrian.trips.xml"
            )

        def run(cmd) -> bool:
            try:
                subprocess.check_output(cmd)
                return True
            except subprocess.CalledProcessError:
                return False
                # raise RuntimeError(
                #     "Command '{}' return with error (code {}): {}".format(
                #         e.cmd, e.returncode, e.output)) from e

        # create vehicle route file
        _ = run(
            [
                "python",
                os.path.join(os.environ["SUMO_HOME"], "tools", "randomTrips.py"),
                "-n",
                net_file,
                "-o",
                trip_files["vehicle"],
                "-r",
                route_files["vehicle"],
                "-b",
                str(self.conf.departure_interval_vehicles.start),
                "-e",
                str(self.conf.departure_interval_vehicles.end),
                "-p",
                str(period),
                "--fringe-factor",
                str(self.conf.fringe_factor),
                "--seed",
                str(self.conf.random_seed_trip_generation),
                "--validate",
                "--additional-file",
                str(self._additional_file),
                '--trip-attributes=departLane="best" departSpeed="max" departPos="random_free"',
            ]
        )
        # create pedestrian routes
        if "pedestrian" in route_files:
            run(
                [
                    "python",
                    os.path.join(os.environ["SUMO_HOME"], "tools", "randomTrips.py"),
                    "-n",
                    net_file,
                    "-o",
                    trip_files["pedestrian"],
                    "-r",
                    route_files["pedestrian"],
                    "-b",
                    str(self.conf.departure_interval_vehicles.start),
                    "-e",
                    str(self.conf.departure_interval_vehicles.end),
                    "-p",
                    str(1 - self.conf.veh_distribution[ObstacleType.PEDESTRIAN]),
                    "--allow-fringe",
                    "--fringe-factor",
                    str(self.conf.fringe_factor),
                    "--persontrips",
                    "--seed",
                    str(self.conf.random_seed_trip_generation),
                    '--trip-attributes= modes="public car" departPos="base"',
                ]
            )

        return route_files

    @staticmethod
    def generate_cfg_file(
        scenario_name: str, net_file: str, route_files: Dict[str, str], output_folder: str
    ) -> str:
        """
        Generates the configuration file according to the scenario name to the specified output folder.

        :param scenario_name: name of the scenario used for the cfg file generation.
        :param net_file: path of the generated sumo .net.xml file
        :param route_files: path of the generated sumo .rou.xml file
        :param output_folder: the generated cfg file will be saved here

        :return: the path of the generated cfg file.
        """

        sumo_cfg_file = os.path.join(output_folder, scenario_name + ".sumo.cfg")
        tree = ET.parse(os.path.join(os.path.dirname(__file__), DEFAULT_CFG_FILE))

        updated_fields = {
            "*/net-file": os.path.basename(net_file),
            "*/route-files": ",".join([os.path.basename(f) for f in route_files.values()]),
        }
        for k, v in updated_fields.items():
            tree.findall(k)[0].attrib["value"] = v

        for elem in tree.iter():
            if elem.text:
                elem.text = elem.text.strip()
            if elem.tail:
                elem.tail = elem.tail.strip()
        rough_string = ET.tostring(tree.getroot(), encoding="utf-8")
        reparsed = minidom.parseString(rough_string)

        with open(sumo_cfg_file, "w") as f:
            f.write(reparsed.toprettyxml(indent="\t", newl="\n"))

        return sumo_cfg_file

    def delete_traffic_light_if_no_intersection(self):
        """
        Delete traffic lights, if lanelet is not an incoming of an intersection.
        :return:
        """
        incoming_mapping = self.lanelet_network.map_inc_lanelets_to_intersections
        for l_id, lanelet in self.lanelet_network._lanelets.items():
            if (
                len(lanelet.traffic_lights) > 0
                and len(lanelet.successor) > 1
                and lanelet not in incoming_mapping
            ):
                lanelet._traffic_lights = set()

        self.lanelet_network.cleanup_traffic_lights()

    def draw_network(self, nodes: Dict[int, Node], edges: Dict[int, Edge], figsize=(20, 20)):
        plt.figure(figsize=figsize)
        draw_params = {
            "lanelet": {"show_label": True},
            "intersection": {"draw_intersections": True, "show_label": True},
        }
        rnd = MPRenderer(draw_params=draw_params)
        self.lanelet_network.draw(rnd)
        rnd.render(show=False)
        G = nx.DiGraph()
        graph_nodes = list(nodes.keys())
        graph_nodes_pos = {node_id: node.coord for node_id, node in nodes.items()}
        for edge_id, edge in edges.items():
            G.add_edge(edge.from_node.id, edge.to_node.id, label=edge.id)
        G.add_nodes_from(graph_nodes)
        nodes = nx.draw_networkx_nodes(G, graph_nodes_pos, node_size=20, nodelist=graph_nodes)
        nx.draw_networkx_edges(G, graph_nodes_pos)
        nx.draw_networkx_labels(G, pos=graph_nodes_pos)
        nodes.set_zorder(800)
        # edges.set_zorder(800)

        nx.draw(G, graph_nodes_pos, with_labels=True)
        colors = itertools.cycle(set(mcolors.TABLEAU_COLORS) - {"tab:blue"})
        for cluster in self.merged_dictionary.values():
            coll = nx.draw_networkx_nodes(
                G, graph_nodes_pos, nodelist=cluster, node_color=next(colors)
            )
            labels = nx.draw_networkx_labels(G, pos=graph_nodes_pos)
            coll.set_zorder(900)
            # for pos

        for inter in self.lanelet_network.intersections:
            s = f"""\
            intersection {inter.intersection_id}:
            inc:{[inc.incoming_lanelets for inc in inter.incomings]}
            out:{list(itertools.chain.from_iterable(
                    [inc.successors_straight | inc.successors_left | inc.successors_right for inc in inter.incomings]))}
            """
            pos = (
                self.lanelet_network.find_lanelet_by_id(
                    list(inter.incomings[0].incoming_lanelets)[0]
                )
                .center_vertices[-1]
                .flatten()
            )
            plt.text(x=pos[0], y=pos[1], s=s, zorder=1e4)
        labels = nx.get_edge_attributes(G, "label")
        nx.draw_networkx_edge_labels(G, pos=graph_nodes_pos, edge_labels=labels)
        plt.autoscale()
        plt.axis("equal")
        plt.show(block=True)
