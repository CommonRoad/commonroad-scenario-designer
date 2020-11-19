from commonroad.scenario.lanelet import LaneletNetwork
from typing import Dict, Set, List, Tuple
from crmapconverter.sumo_map.sumolib_net import Node, Edge
from crmapconverter.sumo_map.sumolib_net.crossing import Crossing
from collections import defaultdict


def get_intersection_clusters(lanelet_network: LaneletNetwork, edges: Dict[int, Edge],
                              lanelet_id2edge_id: Dict[int, int]) -> Tuple[
    Dict[int, Set[Node]], Dict[int, List[Crossing]]]:
    # merged node clustering
    clusters: Dict[int, Set[Node]] = defaultdict(set)
    next_cluster_id = 0
    # crossings are additional info for a cluster
    clusters_crossing: Dict[int, List[Crossing]] = dict()

    for intersection in lanelet_network.intersections:
        intersecting_lanelets = {
            lanelet_id
            for incoming in intersection.incomings
            for lanelet_id in incoming.successors_right
                              | incoming.successors_left
                              | incoming.successors_straight
        }
        intersecting = intersecting_lanelets | intersection.crossings
        intersecting_edges = {
            str(lanelet_id2edge_id[step])
            for step in intersecting
        }
        merged_nodes = {
            node
            for e_id in intersecting_edges for node in
            [edges[e_id].getFromNode(), edges[e_id].getToNode()]
        }
        clusters[next_cluster_id] = merged_nodes

        # generate partial Crossings
        crossings = []
        for lanelet_id in intersection.crossings:
            lanelet = lanelet_network.find_lanelet_by_id(lanelet_id)
            crossings.append(
                Crossing(node=None,
                         edges=None,
                         shape=lanelet.center_vertices,
                         width=3.0))
        if crossings:
            clusters_crossing[next_cluster_id] = crossings

        next_cluster_id += 1

    return clusters, clusters_crossing
