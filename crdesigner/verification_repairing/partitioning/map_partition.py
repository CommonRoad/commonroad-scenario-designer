import enum
import itertools
import logging
import math
from abc import ABC
from functools import reduce
from typing import List, Tuple

import numpy as np
from commonroad.scenario.lanelet import LaneletNetwork

try:
    import pymetis

    pymetis_imported = True
except ImportError:
    pymetis_imported = False

LaneletBlock = List[int]
TrafficSignBlock = List[int]
TrafficLightBlock = List[int]
IntersectionBlock = List[int]
Partition = List[Tuple[LaneletBlock, TrafficLightBlock, TrafficLightBlock, IntersectionBlock]]


class MapPartitioning(ABC):
    """
    The class divides the map into multiple smaller parts. A corresponding partition is generated.
    """

    def __init__(self, network: LaneletNetwork):
        self._network = network

        self._lanelet_ids = [lanelet.lanelet_id for lanelet in self._network.lanelets]
        self._traffic_sign_ids = [
            traffic_sign.traffic_sign_id for traffic_sign in self._network.traffic_signs
        ]
        self._traffic_light_ids = [
            traffic_light.traffic_light_id for traffic_light in self._network.traffic_lights
        ]
        self._intersection_ids = [
            intersection.intersection_id for intersection in self._network.intersections
        ]

    def one_block_partition(self) -> Partition:
        """
        Forms the complete lanelet network as one partition block.

        """
        return [
            (
                self._lanelet_ids,
                self._traffic_sign_ids,
                self._traffic_light_ids,
                self._intersection_ids,
            )
        ]

    @staticmethod
    def _chunks(ids: List[int], size: int):
        """
        Generates chunks with a specified size from a list of IDs.

        :param ids: List of IDs.
        :param size: Size of chunk.
        """
        for i in range(0, len(ids), size):
            yield ids[i : i + size]


@enum.unique
class EdgeType(enum.Enum):
    """Type of edges of the map graph."""

    LEFT_ADJ = "LEFT ADJACENCY"
    RIGHT_ADJ = "RIGHT_ADJACENCY"
    SUCCESSOR = "SUCCESSOR"
    PREDECESSOR = "PREDECESSOR"


MapGraph = List[List[Tuple[int, EdgeType]]]


class LaneletPartitioning(MapPartitioning):
    """
    The class divides the map into multiple smaller parts. A corresponding partition is generated for formulas
    concerning the lanelet element.
    """

    def __init__(self, network: LaneletNetwork):
        super(LaneletPartitioning, self).__init__(network)

        self._node_ids = None
        self._graph = self._create_map_graph()

    def normal_partition(self, ref_size: int, buffered: bool) -> Partition:
        """
        Partitions the map with equally weighted edges.

        :param ref_size: Reference size of partition blocks.
        :param buffered: Boolean indicates whether the lanelets from the buffered area should be inserted.
        :return: Partition.
        """
        v_weights = [1 for _ in range(len(self._graph))]

        number_of_edges = len(reduce(lambda a, b: a + b, self._graph))
        e_weights = [1 for _ in range(number_of_edges)]

        lanelet_partition = self._partition(
            max_size=ref_size, v_weights=v_weights, e_weights=e_weights, buffered=buffered
        )

        lanelet_partition = self._map_lanelet_partition(lanelet_partition)

        partition = [
            (block, self._traffic_sign_ids, self._traffic_light_ids, [])
            for block in lanelet_partition
        ]

        return partition

    def strips_partition(self, ref_size: int, buffered: bool) -> Partition:
        """
        Partitions the map so that a lanelet and its topological left and right adjacencies are in the same
        partition. The edges from a lanelet to its topological adjacencies are weighted maximally.

        :param ref_size: Reference size of partition blocks.
        :param buffered: Boolean indicates whether the lanelets from the buffered area should be inserted.
        :return: Partition.
        """
        v_weights = [1 for _ in range(len(self._graph))]

        e_weights = []
        for edges in self._graph:
            for _, edge_type in edges:
                if edge_type == EdgeType.LEFT_ADJ or edge_type == EdgeType.RIGHT_ADJ:
                    e_weights.append(100)
                else:
                    e_weights.append(1)

        lanelet_partition = self._partition(
            max_size=ref_size, v_weights=v_weights, e_weights=e_weights, buffered=buffered
        )

        for block in lanelet_partition:
            for node_id in block:
                for adj_node_id, edge_type in self._graph[node_id]:
                    if edge_type == EdgeType.LEFT_ADJ or edge_type == EdgeType.RIGHT_ADJ:
                        if adj_node_id not in block:
                            block.append(adj_node_id)

        lanelet_partition = self._map_lanelet_partition(lanelet_partition)

        partition = [
            (block, self._traffic_sign_ids, self._traffic_light_ids, [])
            for block in lanelet_partition
        ]

        logging.info([len(block) for block in lanelet_partition])

        return partition

    def _partition(
        self,
        max_size: int = 25,
        v_weights: List[int] = None,
        e_weights: List[int] = None,
        buffered: bool = False,
    ) -> List[LaneletBlock]:
        """
        Partitions the graph representing the map.

        :param max_size: Maximum size of partition blocks.
        :param buffered: Boolean indicates whether the lanelets from the buffered area should be inserted.
        :return: Partition.
        """
        lanelets = self._network.lanelets

        n_parts = math.ceil(float(len(lanelets)) / float(max_size))

        graph = [[node_id for node_id, _ in node] for node in self._graph]

        xadj = [0]
        pos = 0
        for edges in graph:
            pos = pos + len(edges)
            xadj.append(pos)

        adjncy = list(itertools.chain.from_iterable(graph))

        _, membership = pymetis.part_graph(
            nparts=n_parts, xadj=xadj, adjncy=adjncy, vweights=v_weights, eweights=e_weights
        )

        partition: List[List[int]] = [[] for _ in range(n_parts)]
        for node_id, partition_id in enumerate(membership):
            partition[partition_id].append(node_id)

        if buffered:
            partition = self._add_buffered_area_lanelets(partition, 0.05)

        return partition

    def _create_map_graph(self) -> MapGraph:
        """
        Creates graph of map. Graph is constructed of edges between lanelet and its successors, predecessors,
        left adjacency, and right adjacency.

        :return: Constructed graph.
        """
        lanelets = self._network.lanelets

        graph = [[] for _ in range(len(lanelets))]

        for lan_node_id, lanelet in enumerate(self._network.lanelets):
            if lanelet.successor is not None:
                for successor_id in lanelet.successor:
                    if self._network.find_lanelet_by_id(successor_id) is None:
                        continue
                    adj_node_id = self._get_node_id(successor_id)
                    graph[lan_node_id].append((adj_node_id, EdgeType.SUCCESSOR))

            if lanelet.predecessor is not None:
                for predecessor_id in lanelet.predecessor:
                    if self._network.find_lanelet_by_id(predecessor_id) is None:
                        continue
                    adj_node_id = self._get_node_id(predecessor_id)
                    graph[lan_node_id].append((adj_node_id, EdgeType.PREDECESSOR))

            adj_left_id = lanelet.adj_left
            if (
                adj_left_id is not None
                and self._network.find_lanelet_by_id(adj_left_id) is not None
            ):
                adj_node_id = self._get_node_id(adj_left_id)
                graph[lan_node_id].append((adj_node_id, EdgeType.LEFT_ADJ))

            adj_right_id = lanelet.adj_right
            if (
                adj_right_id is not None
                and self._network.find_lanelet_by_id(adj_right_id) is not None
            ):
                adj_node_id = self._get_node_id(adj_right_id)
                graph[lan_node_id].append((adj_node_id, EdgeType.RIGHT_ADJ))

        graph = [adjs for adjs in graph]

        return graph

    def _get_node_id(self, lanelet_id: int) -> int:
        """
        Maps the lanelet ID to the corresponding node ID.

        :param lanelet_id: Lanelet ID.
        :return: Mapped ID of lanelet; -1 if lanelet cannot be found.
        """
        if self._node_ids is None:
            self._node_ids = {}
            for node_id, lanelet in enumerate(self._network.lanelets):
                self._node_ids.update({lanelet.lanelet_id: node_id})

        return self._node_ids[lanelet_id]

    def _get_lanelet_id(self, node_id: int) -> int:
        """
        Maps the node ID to the corresponding lanelet ID.

        :param node_id: Node ID.
        :return: Mapped ID of node; -1 if node cannot be found.
        """
        lanelets = self._network.lanelets
        if 0 <= node_id < len(lanelets):
            return lanelets[node_id].lanelet_id

        return -1

    def _map_lanelet_partition(self, partition: List[List[int]]) -> List[List[int]]:
        mapped_partition = []
        for block in partition:
            mapped_part = []
            for node_id in block:
                lanelet_id = self._get_lanelet_id(node_id)
                mapped_part.append(lanelet_id)
            mapped_partition.append(mapped_part)

        return mapped_partition

    def _add_buffered_area_lanelets(
        self, partition: List[List[int]], buffer: float
    ) -> List[List[int]]:
        """
        Adds lanelet to the partition if lanelet intersects the buffered area of one of the partitions lanelets.

        :param partition: Partition.
        :return: Extended partition.
        """
        for block in partition:
            lanelets_p = [
                self._network.find_lanelet_by_id(self._get_lanelet_id(node_id)) for node_id in block
            ]
            buffered_areas = [
                lanelet.polygon.shapely_object.buffer(buffer) for lanelet in lanelets_p
            ]

            for lanelet in self._network.lanelets:
                node_id = self._get_node_id(lanelet.lanelet_id)
                if node_id in block:
                    continue

                lanelet_area = lanelet.polygon.shapely_object

                for buffered_area in buffered_areas:
                    if lanelet_area.intersects(buffered_area):
                        block.append(node_id)
                        break

        return partition


class TrafficSignPartitioning(MapPartitioning):
    """
    The class divides the map into multiple smaller parts. A corresponding partition is generated for formulas
    concerning the traffic sign element.
    """

    def __init__(self, network: LaneletNetwork):
        super(TrafficSignPartitioning, self).__init__(network)

    def signs_chunks_partition(self, size: int) -> Partition:
        """
        Partitions all traffic signs in chunks of same size containing only the corresponding referring lanelets.

        :param size: Size of chunk.
        :return: Partition.
        """

        traffic_sign_partition = self._chunks(self._traffic_sign_ids, size)

        traffic_light_ids = []
        intersection_ids = []

        partition = []
        for block in traffic_sign_partition:
            lanelet_ids = []
            for traffic_sign_id in block:
                for lanelet in self._network.lanelets:
                    if traffic_sign_id in lanelet.traffic_signs:
                        lanelet_ids.append(lanelet.lanelet_id)
            partition.append((lanelet_ids, block, traffic_light_ids, intersection_ids))

        return partition


class TrafficLightPartitioning(MapPartitioning):
    """
    The class divides the map into multiple smaller parts. A corresponding partition is generated for formulas
    concerning the traffic light element.
    """

    def __init__(self, network: LaneletNetwork):
        super(TrafficLightPartitioning, self).__init__(network)

    def lights_chunks_partition(self, size: int) -> Partition:
        """
        Partitions all traffic lights in chunks of same size containing only the corresponding referring lanelets.

        :param size: Size of chunk.
        :return: Partition.
        """
        traffic_light_partition = self._chunks(self._traffic_light_ids, size)

        traffic_sign_ids = []
        intersection_ids = []

        partition = []
        for block in traffic_light_partition:
            lanelet_ids = []
            for traffic_light_id in block:
                for lanelet in self._network.lanelets:
                    if traffic_light_id in lanelet.traffic_lights:
                        lanelet_ids.append(lanelet.lanelet_id)
            partition.append((lanelet_ids, traffic_sign_ids, block, intersection_ids))

        return partition


class IntersectionPartitioning(MapPartitioning):
    """
    The class divides the map into multiple smaller parts. A corresponding partition is generated for formulas
    concerning the intersection element.
    """

    def __init__(self, network: LaneletNetwork):
        super(IntersectionPartitioning, self).__init__(network)

    def intersection_chunks_partition(self, size: int) -> Partition:
        """
        Partitions all intersections in chunks of same size containing only the corresponding referring lanelets.

        :param size: Size of chunk.
        :return: Partition.
        """
        intersection_partition = self._chunks(self._intersection_ids, size)

        traffic_sign_ids = []
        traffic_light_ids = []

        partition = []
        for block in intersection_partition:
            lanelet_ids = []
            for intersection_id in block:
                centers = []
                intersection = self._network.find_intersection_by_id(intersection_id)
                if intersection is None:
                    continue
                for incoming in intersection.incomings:
                    for lanelet_id in incoming.incoming_lanelets:
                        lanelet = self._network.find_lanelet_by_id(lanelet_id)
                        if lanelet is None:
                            continue
                        centers.append(lanelet.polygon.center)

                centroid = np.array([0.0, 0.0])
                for center in centers:
                    centroid += center
                centroid /= len(centers)
                proximity_lanelets = self._network.lanelets_in_proximity(centroid, 50.0)
                lanelet_ids.extend([p_l.lanelet_id for p_l in proximity_lanelets])
            partition.append((lanelet_ids, traffic_sign_ids, traffic_light_ids, block))

        return partition
