"""
This module provides a method to offset roads at certain occasions to smooth the course of consecutive lanes.
"""

from crdesigner.common.config.osm_config import osm_config as config
from crdesigner.map_conversion.common import geometry
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations import (
    lane_linker,
)
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations.road_graph._graph import (
    Graph,
)


def offset_graph(graph: Graph) -> None:
    """
    performs an offset on roads in the graph to keep passing lanes straight

    :param graph: the graph to offset
    :return: None
    """
    for node in graph.nodes:
        edges = list(node.edges)
        if node.get_degree() == 2:
            # offsets for roads with changing count of lanes
            for edge, other in [(edges[0], edges[1]), (edges[1], edges[0])]:
                if edge.node1 == node and edge.oneway:
                    _, outgoing = lane_linker.get_incomings_outgoings(edge, node)
                    incoming, _ = lane_linker.get_incomings_outgoings(other, node)
                    if len(incoming) < len(outgoing):
                        # new lanes are created, outgoing edge is set off
                        offset = (
                            (len(outgoing) - len(incoming)) / 2 * config.LANEWIDTHS[edge.roadtype]
                        )
                        if lane_linker.merge_left(incoming, outgoing):
                            offset *= -1
                        edge.interpolated_waypoints = geometry.offset_polyline(
                            edge.interpolated_waypoints, offset, True
                        )
                    elif len(incoming) > len(outgoing):
                        # lanes are removed, incoming edge is set off
                        offset = (
                            (len(incoming) - len(outgoing)) / 2 * config.LANEWIDTHS[edge.roadtype]
                        )
                        if lane_linker.merge_left(incoming, outgoing):
                            offset *= -1
                        other.interpolated_waypoints = geometry.offset_polyline(
                            other.interpolated_waypoints, offset, False
                        )
        if node.get_degree() == 3:
            # offsets for roads splitting off turning lanes
            # edges are sorted counterclockwise
            edges = sorted(node.edges, key=lambda e: e.get_orientation(node))
            for edge_index, edge in enumerate(edges):
                other_edges = edges[edge_index + 1 :] + edges[:edge_index]
                if (
                    edge.node2 == node
                    and edge.oneway
                    and edge.forward_successor is not None
                    and edge.forward_successor.node1 == node
                ):
                    _, outgoing = lane_linker.get_incomings_outgoings(edge.forward_successor, node)
                    incoming, _ = lane_linker.get_incomings_outgoings(edge, node)
                    if edge.forward_successor == other_edges[0]:
                        to_right = True
                    elif edge.forward_successor == other_edges[-1]:
                        to_right = False
                    else:
                        raise ValueError("Graph is malformed")
                    if len(incoming) < len(outgoing):
                        offset = (
                            (len(outgoing) - len(incoming)) / 2 * config.LANEWIDTHS[edge.roadtype]
                        )
                        if not to_right:
                            offset *= -1
                        edge.interpolated_waypoints = geometry.offset_polyline(
                            edge.interpolated_waypoints, offset, False
                        )
                    elif len(incoming) > len(outgoing):
                        offset = (
                            (len(incoming) - len(outgoing)) / 2 * config.LANEWIDTHS[edge.roadtype]
                        )
                        if to_right:
                            offset *= -1
                        edge.interpolated_waypoints = geometry.offset_polyline(
                            edge.interpolated_waypoints, offset, False
                        )
