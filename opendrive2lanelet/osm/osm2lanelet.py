#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Logic to convert OSM to lanelets."""

__author__ = "Benjamin Orthen"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "1.0.2"
__maintainer__ = "Benjamin Orthen"
__email__ = "commonroad-i06@in.tum.de"
__status__ = "Released"


from collections import defaultdict

import numpy as np
from pyproj import Proj
from commonroad.scenario.scenario import Scenario

from opendrive2lanelet.lanelet import ConversionLanelet
from opendrive2lanelet.lanelet_network import ConversionLaneletNetwork
from opendrive2lanelet.osm.osm import OSM

DEFAULT_PROJ_STRING = "+proj=utm +zone=32 +ellps=WGS84"


class OSM2LConverter:
    "Class to convert OSM to the Commonroad representation of Lanelets."

    def __init__(self, proj_string: str = None):
        if proj_string is not None:
            self.proj = Proj(proj_string)
        else:
            self.proj = Proj(DEFAULT_PROJ_STRING)

    def __call__(self, osm: OSM) -> Scenario:
        """Convert OSM to Scenario.

        Args:
          osm: OSM object which includes nodes, ways and lanelet relations.

        Returns:
          A scenario with a lanelet network which describes the
            same map as the osm input.
        """
        scenario = Scenario(dt=0.1, benchmark_id="none")
        lanelet_network = ConversionLaneletNetwork()

        # dicts to save relation of nodes to ways and lanelets
        # so the adjacencies can be determined
        left_way_ids, right_way_ids = dict(), dict()
        first_left_pts, last_left_pts = defaultdict(list), defaultdict(list)
        first_right_pts, last_right_pts = defaultdict(list), defaultdict(list)

        for way_rel in osm.way_relations:
            left_way = osm.find_way_by_id(way_rel.left_way)
            right_way = osm.find_way_by_id(way_rel.right_way)
            left_way_ids[way_rel.left_way] = way_rel.id_
            right_way_ids[way_rel.right_way] = way_rel.id_
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
            for i, node_id in enumerate(left_way.nodes):
                nd = osm.find_node_by_id(node_id)
                x, y = self.proj(float(nd.lon), float(nd.lat))
                if i == 0:
                    first_left_pts[node_id].append(way_rel.id_)
                    first_left_node = node_id
                if i == len_left_way - 1:
                    last_left_node = node_id
                    last_left_pts[node_id].append(way_rel.id_)
                left_vertices[i] = [x, y]
            for i, node_id in enumerate(right_way.nodes):
                nd = osm.find_node_by_id(node_id)
                x, y = self.proj(float(nd.lon), float(nd.lat))
                if i == 0:
                    first_right_node = node_id
                    first_right_pts[node_id].append(way_rel.id_)
                if i == len_right_way - 1:
                    last_right_node = node_id
                    last_right_pts[node_id].append(way_rel.id_)
                right_vertices[i] = [x, y]

            # reverse left vertices if left_way is reversed
            start_dist = np.linalg.norm(left_vertices[0] - right_vertices[0])
            end_dist = np.linalg.norm(left_vertices[0] - right_vertices[-1])
            if start_dist > end_dist:
                left_vertices = left_vertices[::-1]
                first_left_pts, last_left_pts = last_left_pts, first_left_pts
                first_left_node, last_left_node = last_left_node, first_left_node

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

            # check if there are adjacent right and lefts which share a same way
            # and are in the same direction
            potential_right_adj = left_way_ids.get(way_rel.right_way)
            potential_left_adj = right_way_ids.get(way_rel.left_way)
            if potential_right_adj is not None:
                lanelet_network.set_adjacent_right(lanelet, potential_right_adj, True)

            if potential_left_adj is not None:
                lanelet_network.set_adjacent_left(lanelet, potential_left_adj, True)

            # check if there are adjacent right and lefts which share a same way
            # and are in the same direction
            potential_left_adj = left_way_ids.get(way_rel.left_way)
            potential_right_adj = right_way_ids.get(way_rel.right_way)
            if potential_right_adj is not None:
                lanelet_network.set_adjacent_right(lanelet, potential_right_adj, False)

            if potential_left_adj is not None:
                lanelet_network.set_adjacent_left(lanelet, potential_left_adj, False)

            potential_left_successors = last_left_pts.get(first_left_node)
            potential_right_successors = last_right_pts.get(first_right_node)
            if potential_left_successors and potential_right_successors:
                potential_successors = list(
                    set(potential_left_successors) & set(potential_right_successors)
                )
                lanelet_network.add_successors_to_lanelet(lanelet, potential_successors)

            potential_left_predecessors = first_left_pts.get(last_left_node)
            potential_right_predecessors = first_right_pts.get(last_right_node)
            if potential_left_predecessors and potential_right_predecessors:
                potential_predecessors = list(
                    set(potential_left_predecessors) & set(potential_right_predecessors)
                )
                lanelet_network.add_predecessors_to_lanelet(
                    lanelet, potential_predecessors
                )

            # joining and splitting lanelets have to be adjacent rights or lefts
            # splitting lanelets share both starting points and one last point
            # joining lanelets share two last points and one start point
            potential_split_start_left = first_left_pts.get(first_left_node, [])
            potential_split_start_right = first_right_pts.get(first_right_node, [])
            potential_split_end_left = last_right_pts.get(last_left_node, [])
            potential_adj_left = list(
                set(potential_split_start_left)
                & set(potential_split_start_right)
                & set(potential_split_end_left)
            )
            if potential_adj_left:
                lanelet_network.set_adjacent_left(lanelet, potential_adj_left[0])
                # lanelet.adj_left = potential_adj_left[0]
            else:
                potential_split_end_right = last_left_pts.get(last_right_node, [])
                potential_adj_right = list(
                    set(potential_split_start_left)
                    & set(potential_split_start_right)
                    & set(potential_split_end_right)
                )
                if potential_adj_right:
                    lanelet_network.set_adjacent_right(lanelet, potential_adj_right[0])

            lanelet_network.add_lanelet(lanelet)

        lanelet_network.convert_all_lanelet_ids()
        scenario.add_objects(lanelet_network)

        return scenario
