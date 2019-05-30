#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Logic to convert OSM to lanelets."""

__author__ = "Benjamin Orthen"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "1.0.3"
__maintainer__ = "Benjamin Orthen"
__email__ = "commonroad-i06@in.tum.de"
__status__ = "Released"


from collections import defaultdict
from typing import Tuple, List

import numpy as np
from pyproj import Proj
from commonroad.scenario.scenario import Scenario

from opendrive2lanelet.lanelet import ConversionLanelet
from opendrive2lanelet.lanelet_network import ConversionLaneletNetwork
from opendrive2lanelet.osm.osm import OSM, WayRelation

DEFAULT_PROJ_STRING = "+proj=utm +zone=32 +ellps=WGS84"


class OSM2LConverter:
    "Class to convert OSM to the Commonroad representation of Lanelets."

    def __init__(self, proj_string: str = None):
        if proj_string is not None:
            self.proj = Proj(proj_string)
        else:
            self.proj = Proj(DEFAULT_PROJ_STRING)

        # dicts to save relation of nodes to ways and lanelets
        # so the adjacencies can be determined
        self._left_way_ids, self.right_way_ids = dict(), dict()
        self.first_left_pts, self.last_left_pts = defaultdict(list), defaultdict(list)
        self.first_right_pts, self.last_right_pts = defaultdict(list), defaultdict(list)

    def __call__(self, osm: OSM) -> Scenario:
        """Convert OSM to Scenario.

        For each lanelet in OSM format, we have to save their first and last
        point of the left and right boundaries to determine their predecessors,
        successors and adjacent neighbors.

        Args:
          osm: OSM object which includes nodes, ways and lanelet relations.

        Returns:
          A scenario with a lanelet network which describes the
            same map as the osm input.
        """
        scenario = Scenario(dt=0.1, benchmark_id="none")
        lanelet_network = ConversionLaneletNetwork()

        for way_rel in osm.way_relations:
            lanelet = self._way_rel_to_lanelet(way_rel, osm, lanelet_network)
            lanelet_network.add_lanelet(lanelet)

        lanelet_network.convert_all_lanelet_ids()
        scenario.add_objects(lanelet_network)

        return scenario

    def _way_rel_to_lanelet(
        self, way_rel: WayRelation, osm: OSM, lanelet_network: ConversionLaneletNetwork
    ) -> ConversionLanelet:
        """Convert a WayRelation to a Lanelet, add additional adjacency information.

        The ConversionLaneletNetwork saves the adjacency and predecessor/successor
        information.

        Args:
          way_rel: Relation of OSM to convert to Lanelet.
          osm: OSM object which contains info about nodes and ways.
          lanelet_network: Network of which lanelets are part of.

        Returns:
          A lanelet with a right and left vertice.
        """
        left_way = osm.find_way_by_id(way_rel.left_way)
        right_way = osm.find_way_by_id(way_rel.right_way)
        self._left_way_ids[way_rel.left_way] = way_rel.id_
        self.right_way_ids[way_rel.right_way] = way_rel.id_
        left_vertices, right_vertices = (
            np.empty((len(left_way.nodes), 2)),
            np.empty((len(right_way.nodes), 2)),
        )
        len_left_way = len(left_way.nodes)
        len_right_way = len(right_way.nodes)
        if len_left_way != len_right_way:
            print(
                f"Error: Relation {way_rel.id_} has left and right ways which are not equally long!"
            )
            return None

        left_vertices = self._convert_way_to_vertices(left_way, osm)
        first_left_node = left_way.nodes[0]
        last_left_node = left_way.nodes[-1]

        right_vertices = self._convert_way_to_vertices(right_way, osm)
        first_right_node = right_way.nodes[0]
        last_right_node = right_way.nodes[-1]

        # for i, node_id in enumerate(right_way.nodes):
        #     nd = osm.find_node_by_id(node_id)
        #     x, y = self.proj(float(nd.lon), float(nd.lat))
        #     if i == 0:
        #         first_right_node = node_id
        #         self.first_right_pts[node_id].append(way_rel.id_)
        #     if i == len_right_way - 1:
        #         last_right_node = node_id
        #         self.last_right_pts[node_id].append(way_rel.id_)
        #     right_vertices[i] = [x, y]

        # reverse left vertices if left_way is reversed
        start_dist = np.linalg.norm(left_vertices[0] - right_vertices[0])
        end_dist = np.linalg.norm(left_vertices[0] - right_vertices[-1])
        if start_dist > end_dist:
            left_vertices = left_vertices[::-1]
            first_left_node, last_left_node = (last_left_node, first_left_node)

        self.first_left_pts[first_left_node].append(way_rel.id_)
        self.last_left_pts[last_left_node].append(way_rel.id_)
        self.first_right_pts[first_right_node].append(way_rel.id_)
        self.last_right_pts[last_right_node].append(way_rel.id_)

        center_vertices = np.array(
            [(l + r) / 2 for (l, r) in zip(left_vertices, right_vertices)]
        )
        lanelet = ConversionLanelet(
            left_vertices=left_vertices,
            center_vertices=center_vertices,
            right_vertices=right_vertices,
            lanelet_id=way_rel.id_,
            parametric_lane_group=None,
        )

        self._check_right_and_left_neighbors(way_rel, lanelet, lanelet_network)

        potential_successors = self._check_for_successors(
            first_left_node, first_right_node
        )
        lanelet_network.add_successors_to_lanelet(lanelet, potential_successors)

        potential_predecessors = self._check_for_predecessors(
            last_left_node, last_right_node
        )
        lanelet_network.add_predecessors_to_lanelet(lanelet, potential_predecessors)

        # joining and splitting lanelets have to be adjacent rights or lefts
        # splitting lanelets share both starting points and one last point
        # joining lanelets share two last points and one start point
        potential_split_start_left = self.first_left_pts.get(first_left_node, [])
        potential_split_start_right = self.first_right_pts.get(first_right_node, [])
        potential_split_end_left = self.last_right_pts.get(last_left_node, [])
        potential_adj_left = list(
            set(potential_split_start_left)
            & set(potential_split_start_right)
            & set(potential_split_end_left)
        )
        if potential_adj_left:
            lanelet_network.set_adjacent_left(lanelet, potential_adj_left[0])
        else:
            potential_split_end_right = self.last_left_pts.get(last_right_node, [])
            potential_adj_right = list(
                set(potential_split_start_left)
                & set(potential_split_start_right)
                & set(potential_split_end_right)
            )
            if potential_adj_right:
                lanelet_network.set_adjacent_right(lanelet, potential_adj_right[0])

        # TODO: join has to implemented as well

        return lanelet

    def _check_for_successors(
        self, first_left_node: str, first_right_node: str
    ) -> List:
        """Check whether the first left and right node are last nodes of another lanelet.

        Args:
          first_left_node: Id of a node which is at the start of the left way.
          first_right_node: Id of a node which is at the start of the right way.

        Returns:
          List of ids of lanelets where the nodes are at their end.
        """
        potential_left_successors = self.last_left_pts.get(first_left_node)
        potential_right_successors = self.last_right_pts.get(first_right_node)
        if potential_left_successors and potential_right_successors:
            potential_successors = list(
                set(potential_left_successors) & set(potential_right_successors)
            )
            return potential_successors

        return []

    def _check_for_predecessors(
        self, last_left_node: str, last_right_node: str
    ) -> List:
        """Check whether the last left and right node are first nodes of another lanelet.

        Args:
          last_left_node: Id of a node which is at the end of the left way.
          last_right_node: Id of a node which is at the end of the right way.

        Returns:
          List of ids of lanelets where the nodes are at their end.
        """
        potential_left_predecessors = self.first_left_pts.get(last_left_node)
        potential_right_predecessors = self.first_right_pts.get(last_right_node)
        if potential_left_predecessors and potential_right_predecessors:
            potential_predecessors = list(
                set(potential_left_predecessors) & set(potential_right_predecessors)
            )
            return potential_predecessors

        return []

    def _check_right_and_left_neighbors(
        self,
        way_rel: WayRelation,
        lanelet: ConversionLanelet,
        lanelet_network: ConversionLaneletNetwork,
    ):
        """check if lanelet has adjacent right and lefts.

        Determines it by checking if they share a common way.

        Args:
          way_rel: Relation from which lanelet was created.
          lanelet: Lanelet for which to check adjacencies.
          lanelet_network: Network where adjacencies are saved.
        """
        potential_right_adj = self._left_way_ids.get(way_rel.right_way)
        potential_left_adj = self.right_way_ids.get(way_rel.left_way)
        if potential_right_adj is not None:
            lanelet_network.set_adjacent_right(lanelet, potential_right_adj, True)

        if potential_left_adj is not None:
            lanelet_network.set_adjacent_left(lanelet, potential_left_adj, True)

        # check if there are adjacent right and lefts which share a same way
        # and are in the opposite direction
        potential_left_adj = self._left_way_ids.get(way_rel.left_way)
        potential_right_adj = self.right_way_ids.get(way_rel.right_way)
        if potential_right_adj is not None:
            lanelet_network.set_adjacent_right(lanelet, potential_right_adj, False)

        if potential_left_adj is not None:
            lanelet_network.set_adjacent_left(lanelet, potential_left_adj, False)

    def _convert_way_to_vertices(self, way, osm) -> np.ndarray:
        """Convert a Way to a list of points.

        Args:
          way: Way to be converted.
          osm: OSM which includes the way and the nodes.
        Returns:
          The vertices of the new lanelet border.

        """
        # len_way = len(way.nodes)
        vertices = np.empty((len(way.nodes), 2))
        for i, node_id in enumerate(way.nodes):
            nd = osm.find_node_by_id(node_id)
            x, y = self.proj(float(nd.lon), float(nd.lat))
            vertices[i] = [x, y]

        return vertices
