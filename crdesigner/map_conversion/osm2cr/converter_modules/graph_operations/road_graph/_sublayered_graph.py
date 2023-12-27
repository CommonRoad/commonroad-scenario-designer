"""
Sublayered Graph class
"""

from typing import List, Optional, Set, Tuple

from pyproj import Transformer

from ._graph import Graph
from ._graph_edge import GraphEdge
from ._graph_node import GraphNode
from ._graph_traffic_light import GraphTrafficLight
from ._graph_traffic_sign import GraphTrafficSign


class SublayeredGraph(Graph):
    def __init__(
        self,
        nodes: Set[GraphNode],
        edges: Set[GraphEdge],
        center_point: Tuple[float, float],
        bounds: Tuple[float, float, float, float],
        transformer: Transformer,
        traffic_signs: List[GraphTrafficSign],
        traffic_lights: List[GraphTrafficLight],
        sublayer_graph: Graph,
    ):
        super().__init__(
            nodes, edges, center_point, bounds, transformer, traffic_signs, traffic_lights
        )
        # graph that is connected by crossings only (e.g. pedestrian path)
        self.sublayer_graph = sublayer_graph
        self.apply_on_sublayer = True

    def make_contiguous(self) -> None:
        # TODO respective crossing nodes
        super().make_contiguous()
        if self.apply_on_sublayer:
            self.sublayer_graph.make_contiguous()

    def link_edges(self) -> None:
        super().link_edges()
        if self.apply_on_sublayer:
            self.sublayer_graph.link_edges()

    def create_lane_waypoints(self) -> None:
        super().create_lane_waypoints()
        if self.apply_on_sublayer:
            self.sublayer_graph.create_lane_waypoints()

    def interpolate(self) -> None:
        super().interpolate()
        if self.apply_on_sublayer:
            self.sublayer_graph.interpolate()

    def create_lane_link_segments(self) -> None:
        super().create_lane_link_segments()
        if self.apply_on_sublayer:
            self.sublayer_graph.create_lane_link_segments()

    def create_lane_bounds(self, interpolation_scale: Optional[float] = None) -> None:
        super().create_lane_bounds(interpolation_scale)
        if self.apply_on_sublayer:
            self.sublayer_graph.create_lane_bounds(interpolation_scale)

    def correct_start_end_points(self) -> None:
        super().correct_start_end_points()
        if self.apply_on_sublayer:
            self.sublayer_graph.correct_start_end_points()

    def apply_traffic_signs(self) -> None:
        super().apply_traffic_signs()
        if self.apply_on_sublayer:
            self.sublayer_graph.apply_traffic_signs()

    def apply_traffic_lights(self) -> None:
        super().apply_traffic_lights()
        if self.apply_on_sublayer:
            self.sublayer_graph.apply_traffic_lights()

    def delete_invalid_lanes(self) -> None:
        super().delete_invalid_lanes()
        if self.apply_on_sublayer:
            self.sublayer_graph.delete_invalid_lanes()
