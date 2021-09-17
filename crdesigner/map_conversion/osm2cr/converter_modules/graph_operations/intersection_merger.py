"""
This module brings the functionality to merge intersections which are very close together.
This occurs sometimes at large intersection in OSM.
It was, however, found, that this module is often not very useful.
"""
from queue import Queue
from typing import Set, Tuple

import numpy as np

from crdesigner.map_conversion.osm2cr import config
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations import road_graph as rg
from crdesigner.map_conversion.osm2cr.converter_modules.utility import idgenerator as id_gen


def redirect_edges(
    edges: Set[rg.GraphEdge], nodes: Set[rg.GraphNode], node: rg.GraphNode
) -> None:
    """
    changes all nodes, which are in a set of nodes, of edges to a certain node

    :param edges: the edges to redirect
    :param nodes: the nodes from which the edges are redirected
    :param node: the node to redirect to
    :return: None
    """
    for edge in edges:
        if edge.node1 in nodes:
            edge.exchange_node(edge.node1, node)
        if edge.node2 in nodes:
            edge.exchange_node(edge.node2, node)
    return


def get_all_edges(nodes: Set[rg.GraphNode]) -> Set[rg.GraphEdge]:
    """
    gets all edges connected to a set of nodes

    :param nodes: the set of nodes
    :return: None
    """
    res = set()
    for node in nodes:
        res |= node.edges
    return res


def collect_neighbors(node: rg.GraphNode, distance: float) -> Set[rg.GraphNode]:
    """
    collects the set of all near nodes which have at most distance 'distance' to
    each other and have a degree of four

    :param node: to node to start at
    :param distance: the maximal distance of the node
    :return: Set of nodes
    """
    # TODO find a better criterion for merged nodes than distance and degree of four
    explore_queue = Queue()
    for neighbor in node.get_neighbors():
        explore_queue.put(neighbor)
    merge_with = {node}
    visited = {node} | node.get_neighbors()
    while not explore_queue.empty():
        current_node = explore_queue.get()
        if node.get_distance(current_node) < distance:
            """and current_node.get_degree() == 4"""
            merge_with.add(current_node)
            to_explore = current_node.get_neighbors() - visited
            visited |= to_explore
            for new_node in to_explore:
                explore_queue.put(new_node)
    return merge_with


def merge_nodes(
    nodes: Set[rg.GraphNode]
) -> Tuple[rg.GraphNode, Set[rg.GraphEdge], Set[rg.GraphNode]]:
    """
    merges a set of nodes to one

    :param nodes: set of nodes which are merged
    :return: Tuple of 1. the new node, 2. the edges which can be deleted, 3. the nodes which can be deleted
    """
    central_point = np.array([0.0, 0.0])
    for node in nodes:
        central_point += node.get_cooridnates()
    central_point /= len(nodes)

    edges_to_delete = set()
    edges = get_all_edges(nodes)
    for edge in edges:
        if edge.node1 in nodes and edge.node2 in nodes:
            edges_to_delete.add(edge)
    edges -= edges_to_delete

    new_node = rg.GraphNode(id_gen.get_id(), central_point[0], central_point[1], edges)

    redirect_edges(edges, nodes, new_node)

    nodes_to_delete = nodes

    return new_node, edges_to_delete, nodes_to_delete


def merge_close_intersections(graph: rg.Graph) -> None:
    """
    merges close graph nodes

    :param graph: the graph containing the nodes
    :return: None
    """
    updated = True
    if len(graph.nodes) == 0:
        return
    while updated:
        for node in graph.nodes:
            if node.get_degree() == 4 or True:
                updated = False
                nodes_to_merge = collect_neighbors(node, config.MERGE_DISTANCE)
                if len(nodes_to_merge) > 1:
                    new_node, edges_to_delete, nodes_to_delete = merge_nodes(
                        nodes_to_merge
                    )
                    graph.nodes -= nodes_to_delete
                    graph.edges -= edges_to_delete
                    graph.nodes.add(new_node)
                    updated = True
                    break

    return
