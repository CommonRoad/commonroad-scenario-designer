"""Module to convert a lanelet UTM representation to OSM."""

__author__ = "Benjamin Orthen"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "1.2.0"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad-i06@in.tum.de"
__status__ = "Released"

from typing import List, Tuple

import numpy as np
from pyproj import Proj
from commonroad.scenario.lanelet import Lanelet

from opendrive2lanelet.osm.osm import OSM, Node, Way, WayRelation, DEFAULT_PROJ_STRING

ways_are_equal_tolerance = 0.001


class L2OSMConverter:
    """Class to convert CommonRoad lanelet to the OSM representation."""

    def __init__(self, proj_string):
        if proj_string:
            self.proj = Proj(proj_string)
        else:
            self.proj = Proj(DEFAULT_PROJ_STRING)
        self.osm = None
        self._id_count = -1
        self.first_nodes, self.last_nodes = None, None
        self.left_ways, self.right_ways = None, None
        self.lanelet_network = None

    @property
    def id_count(self) -> int:
        """Internal counter for giving IDs to the members of the OSM.

        Each call returns the count and increases it by one.
        Returns:
          Current id count.
        """
        tmp = self._id_count
        self._id_count -= 1
        return tmp

    def __call__(self, scenario):
        """Convert a scenario to an OSM xml document.

        Args:
          scenario:
        """
        self.osm = OSM()
        self.lanelet_network = scenario.lanelet_network
        self.first_nodes = dict()  # saves first left and right node
        self.last_nodes = dict()  # saves last left and right node
        self.left_ways = dict()
        self.right_ways = dict()
        for lanelet in scenario.lanelet_network.lanelets:
            self._convert_lanelet(lanelet)

        return self.osm.serialize_to_xml()

    def _convert_lanelet(self, lanelet: Lanelet):
        """Convert a lanelet to a way relation.

        Add the resulting relation and its ways and nodes to the OSM.

        Args:
          lanelet: Lanelet to be converted.
        """

        # check if there are shared ways
        right_way_id = self._get_potential_right_way(lanelet)
        left_way_id = self._get_potential_left_way(lanelet)

        left_nodes, right_nodes = self._create_nodes(lanelet, left_way_id, right_way_id)

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

    def _create_nodes(
        self, lanelet: Lanelet, left_way_id: str, right_way_id: str
    ) -> Tuple[List[str], List[str]]:
        """Create new nodes for the ways of the lanelet.
        Add them to OSM and return a list of the node ids.

        In case a left or right way already exists, the returned list
        only contains the first and last node of the way.
        Args:
          lanelet: Lanelet of which the right and left vertices should be converted to ways.
          left_way_id: Id of a potential shared left way which was already converted.
            If this is not None, the left vertices of the lanelet do not have to be converted again.
          right_way_id: Id of a potential right way, similar to left_way_id.
        Returns:
          A tuple of lists of node ids for the left and the right way.
        """
        left_nodes, right_nodes = [], []
        start_index = 0
        end_index = len(lanelet.left_vertices)
        pot_first_left_node, pot_first_right_node = self._get_shared_first_nodes_from_other_lanelets(
            lanelet
        )
        pot_last_left_node, pot_last_right_node = self._get_shared_last_nodes_from_other_lanelets(
            lanelet
        )
        if pot_first_left_node:
            start_index = 1
        if pot_last_left_node:
            end_index = -1

        if left_way_id:
            first_left_node, last_left_node = self._get_first_and_last_nodes_from_way(
                left_way_id, lanelet.adj_left_same_direction
            )
        else:
            first_left_node = pot_first_left_node
            last_left_node = pot_last_left_node
            left_nodes = self._create_nodes_from_vertices(
                lanelet.left_vertices[start_index:end_index]
            )
        if right_way_id:
            first_right_node, last_right_node = self._get_first_and_last_nodes_from_way(
                right_way_id, lanelet.adj_right_same_direction
            )
        else:
            first_right_node = pot_first_right_node
            last_right_node = pot_last_right_node
            right_nodes = self._create_nodes_from_vertices(
                lanelet.right_vertices[start_index:end_index]
            )

        if first_left_node:
            left_nodes.insert(0, first_left_node)
        if first_right_node:
            right_nodes.insert(0, first_right_node)

        if last_left_node:
            left_nodes.append(last_left_node)
        if last_right_node:
            right_nodes.append(last_right_node)

        return left_nodes, right_nodes

    def _get_first_and_last_nodes_from_way(
        self, way_id: str, same_dir: bool
    ) -> Tuple[str, str]:
        """Get the first and the last node of a way.

        Reverse order of nodes if way is reversed.
        Args:
          way_id: Id of way.
          same_dir: True if way is in normal direction, False if it is reversed.
        Returns:
          Tuple with first and last node.
        """
        way = self.osm.find_way_by_id(way_id)
        first_idx, last_idx = (0, -1) if same_dir else (-1, 0)
        return (way.nodes[first_idx], way.nodes[last_idx])

    def _create_nodes_from_vertices(self, vertices: List[np.ndarray]) -> List[str]:
        """Create nodes and add them to the OSM.

        Args:
          vertices: List of vertices from a lanelet boundary.
        Returns:
          Ids of nodes which were created.
        """
        nodes = []
        for vertice in vertices:
            lon, lat = self.proj(vertice[0], vertice[1], inverse=True)
            node = Node(self.id_count, lat, lon)
            nodes.append(node.id_)
            self.osm.add_node(node)
        return nodes

    def _get_potential_right_way(self, lanelet):
        """Check if a shared right boundary with another lanelet can be transformed
            to the same way.

        Args:
          lanelet: Lanelet of which right boundary should be converted to a way.
        Returns:
          Id of a way which can be shared, else None if it is not possible.
        """
        if lanelet.adj_right:
            if lanelet.adj_right_same_direction:
                potential_right_way = self.left_ways.get(lanelet.adj_right)
            else:
                potential_right_way = self.right_ways.get(lanelet.adj_right)
            if potential_right_way:
                adj_right = self.lanelet_network.find_lanelet_by_id(lanelet.adj_right)
                vertices = (
                    adj_right.left_vertices
                    if lanelet.adj_right_same_direction
                    else adj_right.right_vertices[::-1]
                )
                if _vertices_are_equal(lanelet.right_vertices, vertices):
                    return potential_right_way

        return None

    def _get_potential_left_way(self, lanelet):
        """Check if a shared left boundary with another lanelet can be transformed
            to the same way.

        Args:
          lanelet: Lanelet of which left boundary should be converted to a way.
        Returns:
          Id of a way which can be shared, else None if it is not possible.
        """
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

    def _get_shared_first_nodes_from_other_lanelets(
        self, lanelet: Lanelet
    ) -> Tuple[str, str]:
        """Get already created nodes from other lanelets which could also
           be used by this lanelet as first nodes.

        Args:
          lanelet: Lanelet for which shared nodes should be found.
        Returns:
          Id of first left and first right node if they exist.
        """
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

    def _get_shared_last_nodes_from_other_lanelets(
        self, lanelet: Lanelet
    ) -> Tuple[str, str]:
        """Get already created nodes from other lanelets which could also
           be used by this lanelet as last nodes.

        Args:
          lanelet: Lanelet for which shared nodes should be found.
        Returns:
          Id of last left and last right node if they exist.
        """
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


def _vertices_are_equal(
    vertices1: List[np.ndarray], vertices2: List[np.ndarray]
) -> bool:
    """Checks if two list of vertices are equal up to a tolerance.

    Args:
      vertices1: First vertices to compare.
      vertices2: Second vertices to compare.

    Returns:
      True if every vertice in one list is nearly equal to the
        corresponding vertices at the same position in the other list.
    """
    if len(vertices1) != len(vertices2):
        return False
    diff = vertices1 - vertices2
    if np.abs(np.max(diff)) < ways_are_equal_tolerance:
        return True
    return False
