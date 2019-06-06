"""Module to convert a lanelet UTM representation to OSM."""

__author__ = "Benjamin Orthen"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "1.0.3"
__maintainer__ = "Benjamin Orthen"
__email__ = "commonroad-i06@in.tum.de"
__status__ = "Released"

import ipdb

import numpy as np
from pyproj import Proj

from opendrive2lanelet.osm.osm import OSM, Node, Way, WayRelation

ways_are_equal_tolerance = 0.001


class L2OSMConverter:
    """Class to convert CommonRoad lanelet to the OSM representation."""

    def __init__(self, proj_string):
        self.proj = Proj(proj_string)
        self.osm = None
        self._id_count = -1
        self.first_left_nodes, self.first_right_nodes = None, None
        self.last_left_nodes, self.last_right_nodes = None, None

    @property
    def id_count(self):
        """Internal counter for giving IDs to the members of the OSM."""
        tmp = self._id_count
        self._id_count -= 1
        return tmp

    def __call__(self, scenario):
        """Convert a scenario to an OSM xml document."""
        self.osm = OSM()
        self.lanelet_network = scenario.lanelet_network
        self.first_nodes = dict()  # saves first left and right node
        self.last_nodes = dict()  # saves last left and right node
        self.left_ways = dict()
        self.right_ways = dict()
        for lanelet in scenario.lanelet_network.lanelets:
            self._convert_lanelet(lanelet)

        return self.osm.serialize_to_xml()

    def _convert_lanelet(self, lanelet):
        """Convert a lanelet to a way relation.

        Args:
          lanelet: Lanelet to be converted.
        """
        start_index = 0
        end_index = len(lanelet.left_vertices)
        left_nodes, right_nodes = [], []
        first_left_node, first_right_node = None, None
        last_left_node, last_right_node = None, None

        # TODO: use right, left way flag and pred succ flag
        # check if there are shared ways
        right_way_id = self._get_potential_right_way(lanelet)
        left_way_id = self._get_potential_left_way(lanelet)
        if left_way_id:
            left_way = self.osm.find_way_by_id(left_way_id)
            if lanelet.adj_left_same_direction:
                first_left_node = left_way.nodes[0]
                last_left_node = left_way.nodes[-1]
            else:
                first_left_node = left_way.nodes[-1]
                last_left_node = left_way.nodes[0]
        if right_way_id:
            right_way = self.osm.find_way_by_id(right_way_id)
            if lanelet.adj_right_same_direction:
                first_right_node = right_way.nodes[0]
                last_right_node = right_way.nodes[-1]
            else:
                first_right_node = right_way.nodes[-1]
                last_right_node = right_way.nodes[0]

        pot_first_left_node, pot_first_right_node = self._get_first_nodes_from_other_lanelets(
            lanelet
        )
        pot_last_left_node, pot_last_right_node = self._get_last_nodes_from_other_lanelets(
            lanelet
        )
        if not left_way_id:
            first_left_node = pot_first_left_node
            last_left_node = pot_last_left_node

        if not right_way_id:
            first_right_node = pot_first_right_node
            last_right_node = pot_last_right_node

        if pot_first_left_node:
            start_index = 1
        if pot_last_left_node:
            end_index = -1

        if first_left_node:
            left_nodes.append(first_left_node)
        if first_right_node:
            right_nodes.append(first_right_node)

        if not left_way_id:
            for vertice in lanelet.left_vertices[start_index:end_index]:
                lon, lat = self.proj(vertice[0], vertice[1], inverse=True)
                node = Node(self.id_count, lat, lon)
                left_nodes.append(node.id_)
                self.osm.add_node(node)

        if not right_way_id:
            for vertice in lanelet.right_vertices[start_index:end_index]:
                lon, lat = self.proj(vertice[0], vertice[1], inverse=True)
                node = Node(self.id_count, lat, lon)
                right_nodes.append(node.id_)
                self.osm.add_node(node)

        if last_left_node:
            left_nodes.append(last_left_node)
        if last_right_node:
            right_nodes.append(last_right_node)

        self.first_nodes[lanelet.lanelet_id] = (left_nodes[0], right_nodes[0])
        self.last_nodes[lanelet.lanelet_id] = (left_nodes[-1], right_nodes[-1])

        if not left_way_id:
            left_way = Way(self.id_count, *left_nodes)
            self.osm.add_way(left_way)
            left_way_id = left_way.id_
        if not right_way_id:
            right_way = Way(self.id_count, *right_nodes)
            self.osm.add_way(right_way)
            right_way_id = right_way.id_

        self.left_ways[lanelet.lanelet_id] = left_way_id
        self.right_ways[lanelet.lanelet_id] = right_way_id
        self.osm.add_way_relation(WayRelation(self.id_count, left_way_id, right_way_id))

    def _get_potential_right_way(self, lanelet):
        """# TODO: return way id and if its in the same direction"""
        if lanelet.adj_right:
            if lanelet.adj_right_same_direction:
                potential_right_way = self.left_ways.get(lanelet.adj_right)
            else:
                potential_right_way = self.right_ways.get(lanelet.adj_right)
                if potential_right_way:
                    adj_right = self.lanelet_network.find_lanelet_by_id(
                        lanelet.adj_right
                    )
                    vertices = (
                        adj_right.left_vertices
                        if lanelet.adj_right_same_direction
                        else adj_right.right_vertices[::-1]
                    )
                    if _vertices_are_equal(lanelet.right_vertices, vertices):
                        return potential_right_way

        return None

    def _get_potential_left_way(self, lanelet):
        if lanelet.adj_left:
            if lanelet.adj_left_same_direction:
                potential_left_way = self.right_ways.get(lanelet.adj_left)
            else:
                potential_left_way = self.left_ways.get(lanelet.adj_left)
                if potential_left_way:
                    adj_left = self.lanelet_network.find_lanelet_by_id(lanelet.adj_left)
                    vertices = (
                        adj_left.right_vertices
                        if lanelet.adj_left_same_direction
                        else adj_left.left_vertices[::-1]
                    )
                    if _vertices_are_equal(lanelet.left_vertices, vertices):
                        return potential_left_way

        return None

    def _get_first_nodes_from_other_lanelets(self, lanelet):
        if lanelet.predecessor:
            for lanelet_id in lanelet.predecessor:
                first_left_node, first_right_node = self.last_nodes.get(
                    lanelet_id, (None, None)
                )
                if first_left_node:
                    return first_left_node, first_right_node
            for pred_id in lanelet.predecessor:
                pred = self.lanelet_network.find_lanelet_by_id(pred_id)
                for succ_id in pred.successor:
                    first_left_node, first_right_node = self.first_nodes.get(
                        succ_id, (None, None)
                    )
                    if first_left_node:
                        return first_left_node, first_right_node
        return None, None

    def _get_last_nodes_from_other_lanelets(self, lanelet):
        if lanelet.successor:
            for lanelet_id in lanelet.successor:
                last_left_node, last_right_node = self.first_nodes.get(
                    lanelet_id, (None, None)
                )
                if last_left_node:
                    return last_left_node, last_right_node
            for succ_id in lanelet.successor:
                succ = self.lanelet_network.find_lanelet_by_id(succ_id)
                for pred_id in succ.predecessor:
                    last_left_node, last_right_node = self.last_nodes.get(
                        pred_id, (None, None)
                    )
                    if last_left_node:
                        return last_left_node, last_right_node

        return None, None


def _vertices_are_equal(vertices1, vertices2) -> bool:
    """Checks if two vertices are equal."""
    if len(vertices1) != len(vertices2):
        return False
    diff = vertices1 - vertices2
    if np.abs(np.max(diff)) < ways_are_equal_tolerance:
        return True
    return False
