# -*- coding: utf-8 -*-

"""Logic to convert OSM to lanelets."""

__author__ = "Benjamin Orthen"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "1.2.0"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad-i06@in.tum.de"
__status__ = "Released"

from collections import defaultdict
from typing import List, Tuple

import numpy as np
from pyproj import Proj
from commonroad.scenario.scenario import Scenario

from opendrive2lanelet.conversion_lanelet import ConversionLanelet
from opendrive2lanelet.conversion_lanelet_network import ConversionLaneletNetwork
from opendrive2lanelet.osm.osm import OSM, WayRelation, DEFAULT_PROJ_STRING

NODE_DISTANCE_TOLERANCE = 0.01  # this is in meters

adjacent_way_distance_tolerance = 0.05


class OSM2LConverter:
    "Class to convert OSM to the Commonroad representation of Lanelets."

    def __init__(self, proj_string: str = None):
        if proj_string is not None:
            self.proj = Proj(proj_string)
        else:
            self.proj = Proj(DEFAULT_PROJ_STRING)
        self._left_way_ids, self._right_way_ids = None, None
        self.first_left_pts, self.last_left_pts = None, None
        self.first_right_pts, self.last_right_pts = None, None
        self.osm = None
        self.lanelet_network = None

    def __call__(
        self,
        osm: OSM,
        detect_adjacencies: bool = True,
        left_driving_system: bool = False,
    ) -> Scenario:
        """Convert OSM to Scenario.

        For each lanelet in OSM format, we have to save their first and last
        point of the left and right boundaries to determine their predecessors,
        successors and adjacent neighbors.

        Args:
          osm: OSM object which includes nodes, ways and lanelet relations.
          detect_adjacencies: Compare vertices which might be adjacent. Set
            to false if you consider it too computationally intensive.
          left_driving_system: Set to true if map describes a left_driving_system.

        Returns:
          A scenario with a lanelet network which describes the
            same map as the osm input.
        """
        # dicts to save relation of nodes to ways and lanelets
        # so the adjacencies can be determined
        self.osm = osm
        self._left_way_ids, self._right_way_ids = defaultdict(list), defaultdict(list)
        self.first_left_pts, self.last_left_pts = defaultdict(list), defaultdict(list)
        self.first_right_pts, self.last_right_pts = defaultdict(list), defaultdict(list)

        scenario = Scenario(dt=0.1, benchmark_id="none")
        self.lanelet_network = ConversionLaneletNetwork()

        for way_rel in osm.way_relations:
            lanelet = self._way_rel_to_lanelet(
                way_rel, detect_adjacencies, left_driving_system
            )
            if lanelet is not None:
                self.lanelet_network.add_lanelet(lanelet)

        self.lanelet_network.convert_all_lanelet_ids()
        scenario.add_objects(self.lanelet_network)

        return scenario

    def _way_rel_to_lanelet(
        self,
        way_rel: WayRelation,
        detect_adjacencies: bool,
        left_driving_system: bool = False,
    ) -> ConversionLanelet:
        """Convert a WayRelation to a Lanelet, add additional adjacency information.

        The ConversionLaneletNetwork saves the adjacency and predecessor/successor
        information.

        Args:
          way_rel: Relation of OSM to convert to Lanelet.
          osm: OSM object which contains info about nodes and ways.
          detect_adjacencies: Compare vertices which might be adjacent. Set
            to false if you consider it too computationally intensive.
          left_driving_system: Set to true if map describes a left_driving_system.

        Returns:
          A lanelet with a right and left vertice.
        """
        left_way = self.osm.find_way_by_id(way_rel.left_way)
        right_way = self.osm.find_way_by_id(way_rel.right_way)
        if len(left_way.nodes) != len(right_way.nodes):
            print(
                f"Error: Relation {way_rel.id_} has left and right ways which are not equally long! Please check your data! Discarding this lanelet relation."
            )
            return None

        # set only if not set before
        # one way can only have two lanelet relations which use it
        if not self._left_way_ids.get(way_rel.left_way):
            self._left_way_ids[way_rel.left_way] = way_rel.id_
        if not self._right_way_ids.get(way_rel.right_way):
            self._right_way_ids[way_rel.right_way] = way_rel.id_

        left_vertices = self._convert_way_to_vertices(left_way)
        first_left_node = left_way.nodes[0]
        last_left_node = left_way.nodes[-1]

        right_vertices = self._convert_way_to_vertices(right_way)
        first_right_node = right_way.nodes[0]
        last_right_node = right_way.nodes[-1]

        start_dist = np.linalg.norm(
            left_vertices[0] - right_vertices[0]
        ) + np.linalg.norm(left_vertices[-1] - right_vertices[-1])
        end_dist = np.linalg.norm(
            left_vertices[0] - right_vertices[-1]
        ) + np.linalg.norm(left_vertices[-1] - right_vertices[0])
        if start_dist > end_dist:
            if left_driving_system:
                # reverse right vertices if right_way is reversed
                right_vertices = right_vertices[::-1]
                first_right_node, last_right_node = (last_right_node, first_right_node)
            else:
                # reverse left vertices if left_way is reversed
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

        self._check_right_and_left_neighbors(way_rel, lanelet)

        if detect_adjacencies:
            self._find_adjacencies_of_coinciding_ways(
                lanelet,
                first_left_node,
                first_right_node,
                last_left_node,
                last_right_node,
            )

        potential_successors = self._check_for_successors(
            last_left_node=last_left_node, last_right_node=last_right_node
        )
        self.lanelet_network.add_successors_to_lanelet(lanelet, potential_successors)

        potential_predecessors = self._check_for_predecessors(
            first_left_node=first_left_node, first_right_node=first_right_node
        )
        self.lanelet_network.add_predecessors_to_lanelet(
            lanelet, potential_predecessors
        )

        potential_adj_left, potential_adj_right = self._check_for_split_and_join_adjacencies(
            first_left_node, first_right_node, last_left_node, last_right_node
        )
        if potential_adj_left:
            self.lanelet_network.set_adjacent_left(lanelet, potential_adj_left[0], True)
        if potential_adj_right:
            self.lanelet_network.set_adjacent_right(
                lanelet, potential_adj_right[0], True
            )

        return lanelet

    def _check_for_split_and_join_adjacencies(
        self, first_left_node, first_right_node, last_left_node, last_right_node
    ) -> Tuple[List, List]:
        """Check if there are adjacencies if there is a lanelet split or join.

        joining and splitting lanelets have to be adjacent rights or lefts
        splitting lanelets share both starting points and one last point
        joining lanelets share two last points and one start point

        Args:
          first_left_node: First node of left way of the lanelet.
          first_right_node: First node of right way of the lanelet.
          last_left_node: Last node of left way of the lanelet.
          last_right_node: Last node of right way of the lanelet.

        Returns:
          A tuple of lists which contain candidates for the
          left and the right adjacency.
        """
        potential_split_start_left = self._find_lanelet_ids_of_suitable_nodes(
            self.first_left_pts, first_left_node
        )
        potential_split_start_right = self._find_lanelet_ids_of_suitable_nodes(
            self.first_right_pts, first_right_node
        )
        potential_split_end_left = self._find_lanelet_ids_of_suitable_nodes(
            self.last_right_pts, last_left_node
        )
        potential_split_end_right = self._find_lanelet_ids_of_suitable_nodes(
            self.last_left_pts, last_right_node
        )

        potential_adj_left = list(
            set(potential_split_start_left)
            & set(potential_split_start_right)
            & set(potential_split_end_left)
        )
        potential_adj_right = list(
            set(potential_split_start_left)
            & set(potential_split_start_right)
            & set(potential_split_end_right)
        )

        if not potential_adj_left or not potential_adj_right:
            potential_join_end_left = self._find_lanelet_ids_of_suitable_nodes(
                self.last_left_pts, last_left_node
            )
            potential_join_end_right = self._find_lanelet_ids_of_suitable_nodes(
                self.last_right_pts, last_right_node
            )

            if not potential_adj_left:
                potential_join_start_left = self._find_lanelet_ids_of_suitable_nodes(
                    self.first_right_pts, first_left_node
                )
                potential_adj_left = list(
                    set(potential_join_start_left)
                    & set(potential_join_end_left)
                    & set(potential_join_end_right)
                )

            if not potential_adj_right:
                potential_join_start_right = self._find_lanelet_ids_of_suitable_nodes(
                    self.first_left_pts, first_right_node
                )
                potential_adj_right = list(
                    set(potential_join_start_right)
                    & set(potential_join_end_left)
                    & set(potential_join_end_right)
                )

        return potential_adj_left, potential_adj_right

    def _check_for_predecessors(
        self, first_left_node: str, first_right_node: str
    ) -> List:

        """Check whether the first left and right node are last nodes of another lanelet.

        Args:
          first_left_node: Id of a node which is at the start of the left way.
          first_right_node: Id of a node which is at the start of the right way.

        Returns:
          List of ids of lanelets where the nodes are at their end.
        """
        potential_left_predecessors = self._find_lanelet_ids_of_suitable_nodes(
            self.last_left_pts, first_left_node
        )
        potential_right_predecessors = self._find_lanelet_ids_of_suitable_nodes(
            self.last_right_pts, first_right_node
        )
        if potential_left_predecessors and potential_right_predecessors:
            potential_predecessors = list(
                set(potential_left_predecessors) & set(potential_right_predecessors)
            )
            return potential_predecessors

        return []

    def _check_for_successors(self, last_left_node: str, last_right_node: str) -> List:
        """Check whether the last left and right node are first nodes of another lanelet.

        Args:
          last_left_node: Id of a node which is at the end of the left way.
          last_right_node: Id of a node which is at the end of the right way.

        Returns:
          List of ids of lanelets where the nodes are at their start.
        """

        potential_left_successors = self._find_lanelet_ids_of_suitable_nodes(
            self.first_left_pts, last_left_node
        )
        potential_right_successors = self._find_lanelet_ids_of_suitable_nodes(
            self.first_right_pts, last_right_node
        )
        if potential_left_successors and potential_right_successors:
            potential_successors = list(
                set(potential_left_successors) & set(potential_right_successors)
            )
            return potential_successors

        return []

    def _find_adjacencies_of_coinciding_ways(
        self,
        lanelet: ConversionLanelet,
        first_left_node: str,
        first_right_node: str,
        last_left_node: str,
        last_right_node: str,
    ):
        """Find adjacencies of a lanelet by checking if its vertices coincide with vertices of other lanelets.

        Set new adjacent left or right if it finds neighbors.

        Args:
          lanelet: Lanelet to check potential adjacencies for.
          first_left_node: Id of first left node of the lanelet relation in OSM.
          first_right_node: Id of first right node of the lanelet relation in OSM.
          last_left_node: Id of last left node of the lanelet relation in OSM.
          last_right_node: Id of last right node of the lanelet relation in OSM.

        """
        # first case: left adjacent, same direction
        if lanelet.adj_left is None:
            potential_left_front = self._find_lanelet_ids_of_suitable_nodes(
                self.first_right_pts, first_left_node
            )
            potential_left_back = self._find_lanelet_ids_of_suitable_nodes(
                self.last_right_pts, last_left_node
            )
            potential_left_same_direction = list(
                set(potential_left_front) & set(potential_left_back)
            )
            for lanelet_id in potential_left_same_direction:
                nb_lanelet = self.lanelet_network.find_lanelet_by_id(lanelet_id)
                if nb_lanelet is not None and _two_vertices_coincide(
                    lanelet.left_vertices, nb_lanelet.right_vertices
                ):
                    self.lanelet_network.set_adjacent_left(
                        lanelet, nb_lanelet.lanelet_id, True
                    )
                    break

        # second case: right adjacent, same direction
        if lanelet.adj_right is None:
            potential_right_front = self._find_lanelet_ids_of_suitable_nodes(
                self.first_left_pts, first_right_node
            )
            potential_right_back = self._find_lanelet_ids_of_suitable_nodes(
                self.last_left_pts, last_right_node
            )
            potential_right_same_direction = list(
                set(potential_right_front) & set(potential_right_back)
            )
            for lanelet_id in potential_right_same_direction:
                nb_lanelet = self.lanelet_network.find_lanelet_by_id(lanelet_id)
                if nb_lanelet is not None and _two_vertices_coincide(
                    lanelet.right_vertices, nb_lanelet.left_vertices
                ):
                    self.lanelet_network.set_adjacent_right(
                        lanelet, nb_lanelet.lanelet_id, True
                    )
                    break

        # third case: left adjacent, opposite direction
        if lanelet.adj_left is None:
            potential_left_front = self._find_lanelet_ids_of_suitable_nodes(
                self.last_left_pts, first_left_node
            )
            potential_left_back = self._find_lanelet_ids_of_suitable_nodes(
                self.first_left_pts, last_left_node
            )
            potential_left_other_direction = list(
                set(potential_left_front) & set(potential_left_back)
            )
            for lanelet_id in potential_left_other_direction:
                nb_lanelet = self.lanelet_network.find_lanelet_by_id(lanelet_id)
                # compare right vertice of nb_lanelet with left vertice of lanelet
                if nb_lanelet is not None and _two_vertices_coincide(
                    lanelet.left_vertices, nb_lanelet.left_vertices[::-1]
                ):
                    self.lanelet_network.set_adjacent_left(
                        lanelet, nb_lanelet.lanelet_id, False
                    )
                    break

        # fourth case: right adjacent, opposite direction
        if lanelet.adj_right is None:
            potential_right_front = self._find_lanelet_ids_of_suitable_nodes(
                self.last_right_pts, first_right_node
            )
            potential_right_back = self._find_lanelet_ids_of_suitable_nodes(
                self.first_right_pts, last_right_node
            )
            potential_right_other_direction = list(
                set(potential_right_front) & set(potential_right_back)
            )
            for lanelet_id in potential_right_other_direction:
                nb_lanelet = self.lanelet_network.find_lanelet_by_id(lanelet_id)
                if nb_lanelet is not None and _two_vertices_coincide(
                    lanelet.right_vertices, nb_lanelet.right_vertices[::-1]
                ):
                    self.lanelet_network.set_adjacent_right(
                        lanelet, nb_lanelet.lanelet_id, True
                    )
                    break

    def _check_right_and_left_neighbors(
        self, way_rel: WayRelation, lanelet: ConversionLanelet
    ):
        """check if lanelet has adjacent right and lefts.

        Determines it by checking if they share a common way.
        Either in opposite or in the same direction.

        Args:
          way_rel: Relation from which lanelet was created.
          lanelet: Lanelet for which to check adjacencies.
        """
        potential_right_adj = self._left_way_ids.get(way_rel.right_way)
        potential_left_adj = self._right_way_ids.get(way_rel.left_way)
        if potential_right_adj is not None:
            self.lanelet_network.set_adjacent_right(lanelet, potential_right_adj, True)

        if potential_left_adj is not None:
            self.lanelet_network.set_adjacent_left(lanelet, potential_left_adj, True)

        # check if there are adjacent right and lefts which share a same way
        # and are in the opposite direction
        if not potential_left_adj:
            potential_left_adj = self._left_way_ids.get(way_rel.left_way)
            if potential_left_adj is not None:
                self.lanelet_network.set_adjacent_left(
                    lanelet, potential_left_adj, False
                )

        if not potential_right_adj:
            potential_right_adj = self._right_way_ids.get(way_rel.right_way)
            if potential_right_adj is not None:
                self.lanelet_network.set_adjacent_right(
                    lanelet, potential_right_adj, False
                )

    def _convert_way_to_vertices(self, way) -> np.ndarray:
        """Convert a Way to a list of points.

        Args:
          way: Way to be converted.
          osm: OSM which includes the way and the nodes.
        Returns:
          The vertices of the new lanelet border.

        """
        vertices = np.empty((len(way.nodes), 2))
        for i, node_id in enumerate(way.nodes):
            nd = self.osm.find_node_by_id(node_id)
            x, y = self.proj(float(nd.lon), float(nd.lat))
            vertices[i] = [x, y]

        return vertices

    def node_distance(self, node_id1: str, node_id2: str) -> float:
        """Calculate distance of one node to other node in the projection.

        Args:
          node_id1: Id of first node.
          node_id2: id of second node.
        Returns:
          Distance in
        """
        node1 = self.osm.find_node_by_id(node_id1)
        node2 = self.osm.find_node_by_id(node_id2)
        vec1 = np.array(self.proj(float(node1.lon), float(node1.lat)))
        vec2 = np.array(self.proj(float(node2.lon), float(node2.lat)))
        return np.linalg.norm(vec1 - vec2)

    def _find_lanelet_ids_of_suitable_nodes(
        self, nodes_dict: dict, node_id: str
    ) -> List:
        """Find values of a dict where the keys are node ids.

        Return the entries if there is a value in the node_dict
        for the node_id, but also the values for nodes which are in
        the proximity of the node with the node_id.

        Args:
          nodes_dict: Dict which saves lanelet ids with node ids as keys.
          node_id: Id of node for which the other entries are searched for.
        Returns:
          List of lanelet ids which match the above-mentioned rules.
        """
        suitable_lanelet_ids = []
        suitable_lanelet_ids.extend(nodes_dict.get(node_id, []))
        for nd, lanelet_ids in nodes_dict.items():
            if self.node_distance(nd, node_id) < NODE_DISTANCE_TOLERANCE:
                suitable_lanelet_ids.extend(lanelet_ids)
        return suitable_lanelet_ids


def _two_vertices_coincide(
    vertices1: List[np.ndarray], vertices2: List[np.ndarray]
) -> bool:
    """Check if two vertices coincide and describe the same trajectory.

    For each vertice of vertices2 the minimal distance to the trajectory
    described by vertices1 is calculated. If this distance crosses a certain
    threshold, the vertices are deemed to be different.

    Args:
      vertices1: List of vertices which describe first trajectory.
      vertices2: List of vertices which describe second trajectory.

    Returns:
      True if the vertices coincide, else False.
    """
    segments = np.diff(vertices1, axis=0)

    for vert in vertices2:
        distances = np.empty([len(vertices1) + 1])
        distances[0] = np.linalg.norm(vert - vertices1[0])
        distances[-1] = np.linalg.norm(vert - vertices1[-1])
        for i, diff in enumerate(segments):
            distances[i + 1] = np.abs(
                np.cross(diff, vertices1[i] - vert)
            ) / np.linalg.norm(diff)
        if np.min(distances) > adjacent_way_distance_tolerance:
            return False

    return True
