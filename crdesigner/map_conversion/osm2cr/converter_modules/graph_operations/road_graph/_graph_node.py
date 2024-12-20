from __future__ import annotations

from typing import TYPE_CHECKING, Set

import numpy as np

from crdesigner.map_conversion.common import geometry
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations.road_graph._graph_traffic_sign import (
    GraphTrafficSign,
)

if TYPE_CHECKING:
    from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations.road_graph._graph_edge import (
        GraphEdge,
    )


class GraphNode:
    """
    Class that represents a node in the graph

    """

    def __init__(self, id: int, x: float, y: float, edges: Set[GraphEdge]):
        """
        creates a graph node

        :param id: unique id of the node
        :param x: x coordinate
        :param y: y coordinate
        :param edges:  set of edges connected to the node
        """
        self.id = id
        self.x = x
        self.y = y
        self.edges = edges
        self.traffic_signs = []
        self.traffic_lights = []
        self.is_crossing = False

    def __str__(self):
        return "Graph_node with id: {}".format(self.id)

    def __repr__(self):
        return "Graph_node with id: {}".format(self.id)

    def get_degree(self) -> int:
        """
        gets the degree of the node

        :return: degree of node
        """
        return len(self.edges)

    def get_cooridnates(self) -> np.ndarray:
        """
        gets coordinates as numpy array

        :return: coordinates in numpy array
        """
        return np.array([self.x, self.y])

    def get_point(self) -> geometry.Point:
        """
        gets a Point object which is located at the node

        :return: a Point object located at the node
        """
        return geometry.Point(None, self.x, self.y)

    def get_distance(self, other: "GraphNode") -> float:
        """
        calculates distance to other node

        :param other: other node
        :return: distance between nodes
        """
        return np.linalg.norm(self.get_cooridnates() - other.get_cooridnates())

    def get_highest_edge_distance(self) -> float:
        """
        gets the highest distance a connected edge has to the node

        :return: highest distance to connected edge
        """
        result = 0.0
        for edge in self.edges:
            if edge.node1 == self:
                distance = np.linalg.norm(
                    edge.get_interpolated_waypoints()[0] - self.get_cooridnates()
                )
            elif edge.node2 == self:
                distance = np.linalg.norm(
                    edge.get_interpolated_waypoints()[-1] - self.get_cooridnates()
                )
            else:
                raise ValueError("Graph is malformed")
            result = max(result, distance)
        return result

    def get_neighbors(self) -> Set["GraphNode"]:
        """
        finds nodes which are connected to this node via a single edge

        :return: set of neighbors
        """
        res = set()
        for edge in self.edges:
            res |= {edge.node1, edge.node2}
        res.discard(self)
        return res

    def set_coordinates(self, position: np.ndarray) -> None:
        """
        sets the coordinates of a node to the position given in a numpy array

        :param position: new position
        :return: None
        """
        self.x = position[0]
        self.y = position[1]

    def move_to(self, position: np.ndarray) -> None:
        """
        moves a node in the graph, also moves the waypoints of all edges which start or end at the node
        WARNING! this method should only be used before the course of the lanes in the graph are generated

        :param position: new position
        :return: None
        """
        self.set_coordinates(position)
        for edge in self.edges:
            if edge.node1 == self:
                edge.waypoints[0].set_position(position)
            elif edge.node2 == self:
                edge.waypoints[-1].set_position(position)
            else:
                raise ValueError(
                    "malformed graph, node has edges assigned to it, which start elsewhere"
                )

    def add_traffic_sign(self, sign: GraphTrafficSign):
        for edge in self.edges:
            for lane in edge.lanes:
                # add to forward lanes
                # TODO determine in which direction
                if lane.forward:
                    lane.add_traffic_sign(
                        sign,
                    )
