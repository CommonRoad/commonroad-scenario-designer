"""
This module provides functions to plot a scenario for a GUI.
The plot objects allow some interaction with them.
All plot functions in this module can plot in cartesian coordinates as well as in latitude and longitude.

"""
from abc import ABC
from typing import Tuple, List, Optional, Set, Dict, Union

import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import Collection, PathCollection
from matplotlib.colors import to_rgba
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrow, Polygon, Patch, PathPatch
from matplotlib.path import Path

from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations import road_graph as rg
from crdesigner.map_conversion.common import geometry

PICKER_SIZE = 2
LINE_WIDTH = 2.5
SCATTER_SIZE = 200
HIGHLIGHT_COLOR = "skyblue"
STANDARD_COLOR = "black"
POINT_COLOR = "dimgrey"
LANE_DIRECTION_COLOR = "blue"
EDGE_DIRECTION_COLOR = "dimgrey"

class InteractiveObject(ABC):
    """
    A custom class for interactive objects in a plot
    Instances can be highlighted and removed from the plot
    Each instance has a pointer to it's matplotlib object plot_object
    """

    def __init__(self, plot_object: Union[Patch, PathCollection, Line2D]):
        """

        :param plot_object: the corresponding matplotlib object
        """
        self.plot_object: Union[Patch, PathCollection, Line2D] = plot_object

    def highlight(self) -> None:
        """
        highlights the plot object by changing its color

        :return: None
        """
        # print("highlighting {}".format(type(self).__name__))
        self.plot_object.set_color(HIGHLIGHT_COLOR)

    def unhighlight(self) -> None:
        """
        removes highlight by changing to default color

        :return: None
        """
        # print("unhighlighting {}".format(type(self).__name__))
        self.plot_object.set_color(None)

    def remove(self) -> None:
        """
        removes the object from the plot

        :return: None
        """
        self.plot_object.remove()

class Link(InteractiveObject):
    """
    Represents a link between two lanes.

    """

    def __init__(self, arrow: FancyArrow, from_lane: rg.Lane, to_lane: rg.Lane):
        """

        :param arrow: plot object
        :param from_lane: predecessor lane
        :param to_lane: successor lane
        """
        super().__init__(arrow)
        self.from_lane = from_lane
        self.to_lane = to_lane

    def remove(self) -> None:
        """
        removes the link as well as the plot of the link

        :return: None
        """
        super().remove()
        self.from_lane.successors.remove(self.to_lane)
        self.to_lane.predecessors.remove(self.from_lane)

class Node(InteractiveObject):
    """
    Plot of set of all nodes
    """

    def __init__(
        self,
        scatter_object: PathCollection,
        node_list: List[rg.GraphNode],
        ax: Axes,
        latlon: bool,
        origin: np.ndarray,
    ):
        """

        :param scatter_object: plot object of nodes
        :param node_list: graph nodes in same order as plot points
        :param ax: Axes on which plot is displayed
        :param latlon: defines whether the nodes are projected in geographic coordinates
        :param origin: the origin of the cartesian coordinate system
        """
        super().__init__(scatter_object)
        self.ax = ax
        self.latlon = latlon
        self.origin = origin
        self.node_list = node_list
        self.highlighted_node: Optional[int] = None

    def highlight(self) -> None:
        """
        the whole set of nodes cannot be highlighted

        :return: None
        """
        raise NotImplementedError("You can only highlight a single node")

    def unhighlight(self) -> None:
        """
        removes highlight from all nodes

        :return: None
        """
        self.plot_object.set_facecolor([STANDARD_COLOR] * len(self.node_list))
        self.highlighted_node = None

    def remove(self) -> None:
        """
        deleting all nodes at once is not possible

        :return:
        """
        raise NotImplementedError("Nodes cannot be removed all at once")

    def highlight_single_node(self, index: int) -> int:
        """
        highlights only a single node

        :param index: index of the node to highlight
        :return: index of the node to highlight
        """
        self.plot_object._facecolors[index, :] = to_rgba(HIGHLIGHT_COLOR)
        self.highlighted_node = index
        return index

    def redraw(self) -> None:
        """
        removes and draws all nodes new

        :return: None
        """
        self.plot_object.remove()
        self.draw()

    def draw(self) -> None:
        """
        draws all nodes

        :return: None
        """
        node_points = np.array(
            [node.get_point().get_array() for node in self.node_list]
        )
        if self.latlon:
            node_points = geometry.cartesian_to_lon_lat(node_points.T, self.origin).T
        scatter_object = self.ax.scatter(
            node_points[:, 0],
            node_points[:, 1],
            picker=PICKER_SIZE,
            color=[STANDARD_COLOR] * len(self.node_list),
            s=SCATTER_SIZE,
        )
        scatter_object.ref = self
        self.plot_object = scatter_object
        if self.highlighted_node is not None:
            self.highlight_single_node(self.highlighted_node)

class PointList(InteractiveObject):
    """
    List of plotted points.
    Used for way points of edges.
    """

    def __init__(self, scatter_object: PathCollection, nr_of_points: int):
        """

        :param scatter_object: plot object of points
        :param nr_of_points: count of points in the plot object
        """
        super().__init__(scatter_object)
        self.last_picked_point_index: Optional[int] = None
        self.nr_of_points = nr_of_points

    def highlight(self) -> None:
        """
        the whole set of points cannot be highlighted

        :return: None
        """
        raise NotImplementedError("You can only highlight a single point")

    def unhighlight(self) -> None:
        """
        removes highlight from all points

        :return: None
        """
        self.plot_object.set_facecolor([POINT_COLOR] * self.nr_of_points)

    def highlight_single_point(self, index: int) -> None:
        """
        highlights only a single point

        :param index: index of the point to highlight
        :return: None
        """
        self.plot_object._facecolors[index, :] = to_rgba(HIGHLIGHT_COLOR)

class Edge(InteractiveObject):
    """
    Used for plot of an edge.
    """

    def __init__(
        self,
        polyline: Line2D,
        edge: rg.GraphEdge,
        graph: rg.Graph,
        latlon: bool,
        ax: Axes,
        origin: np.ndarray,
    ):
        """

        :param polyline: plot object of line
        :param edge: graph edge
        :param graph: graph containing the edge
        :param latlon: defines whether the nodes are projected in geographic coordinates
        :param ax: Axes on which plot is displayed
        :param origin: the origin of the cartesian coordinate system
        """
        super().__init__(polyline)
        self.edge = edge
        self.graph = graph
        self.latlon = latlon
        self.ax = ax
        self.origin = origin
        self.waypoint_plot: Optional[PointList] = None
        self.highlight_patches: Set[Patch] = set()

    def highlight(self) -> None:
        """
        highlights the edge,
        adds also visualization of all lanes, their direction and the direction and waypoints of the edge

        :return: None
        """
        self.remove_highlight_patches()
        super().highlight()
        self.draw_waypoints()
        self.update_lanes_and_dir()
        # self.ax.figure.canvas.draw() # this is done in update_lanes_and_dir()

    def update_lanes_and_dir(self) -> None:
        """
        draws the lanes of the edge with a triangle for their direction each
        draws also a triangle for the direction of the edge

        :return: None
        """
        self.remove_highlight_patches()
        dir_triangle = self.direction_triangle(
            self.edge.get_waypoints(),
            self.edge.lanewidth * 2,
            self.origin,
            EDGE_DIRECTION_COLOR,
        )
        self.highlight_patches.add(dir_triangle)
        self.draw_lanes()
        self.add_patches_to_ax()
        self.ax.figure.canvas.draw()

    def add_patches_to_ax(self) -> None:
        """
        adds the patched which are created for highlighting to the axes,
        does not perform a redraw -> patches cannot be seen directly

        :return: None
        """
        for patch in self.highlight_patches:
            self.ax.add_patch(patch)

    def unhighlight(self) -> None:
        """
        removes highlight from edge

        :return: None
        """
        self.plot_object.set_color(STANDARD_COLOR)
        # hide all waypoints
        if self.waypoint_plot is not None:
            self.waypoint_plot.remove()
            self.waypoint_plot = None
        self.remove_highlight_patches()

    def remove_highlight_patches(self) -> None:
        """
        removes the addiotional patches from the axes

        :return: None
        """
        for patch in self.highlight_patches:
            patch.remove()
        self.highlight_patches = set()

    def remove(self) -> None:
        """
        deletes the edge

        :return: None
        """
        self.unhighlight()
        super().remove()
        self.graph.remove_edge(self.edge)
        # hide all waypoints
        if self.waypoint_plot is not None:
            self.waypoint_plot.remove()
            self.waypoint_plot = None

    def draw_waypoints(self) -> None:
        """
        draws the waypoints of the edge

        :return: None
        """
        waypoints = geometry.points_to_array(self.edge.waypoints)[1:-1]
        if len(waypoints) == 0:
            return
        if self.latlon:
            waypoints = geometry.cartesian_to_lon_lat(
                waypoints.T, self.graph.center_point
            ).T
        # draw all waypoints
        scatter_object = self.ax.scatter(
            waypoints[:, 0],
            waypoints[:, 1],
            picker=PICKER_SIZE,
            color=[POINT_COLOR] * len(waypoints),
            s=SCATTER_SIZE,
        )

        self.waypoint_plot = PointList(scatter_object, len(waypoints))
        scatter_object.ref = self.waypoint_plot

    def draw_lanes(self) -> None:
        """
        draws lanes of the edge

        :return: None
        """
        lane_waypoints = rg.get_lane_waypoints(
            self.edge.nr_of_lanes,
            self.edge.lanewidth,
            self.edge.get_interpolated_waypoints(False),
        )
        assert len(self.edge.lanes) == self.edge.nr_of_lanes
        for i, waypoints in enumerate(lane_waypoints):
            line = [geometry.cartesian_to_lon_lat(p, self.origin) for p in waypoints]
            assert self.edge.lanes[i].forward is not None
            if not self.edge.lanes[i].forward:
                line = line[::-1]
                waypoints = waypoints[::-1]
            dir_triangle = self.direction_triangle(
                np.array(waypoints),
                self.edge.lanewidth,
                self.origin,
                LANE_DIRECTION_COLOR,
            )
            self.highlight_patches.add(dir_triangle)
            line = Path(np.array(line), closed=False)
            self.highlight_patches.add(PathPatch(line, fill=False))

    @staticmethod
    def direction_triangle(
        line: np.ndarray, width: float, origin: np.ndarray, color: str
    ) -> Polygon:
        """
        creates a triangle to visualize direction of the line

        :param line:  line to visualize
        :param width: width of the trianlge
        :param origin: origin of the cartesian coordinate system
        :param color: color of the patch
        :return: the polygon
        """
        direction_vector = line[1] - line[0]
        direction_vector /= np.linalg.norm(direction_vector)
        orthogonal_vector = geometry.get_orthogonal(direction_vector)
        p1 = line[0] + orthogonal_vector * width / 2
        p2 = line[0] - orthogonal_vector * width / 2
        p3 = line[0] + direction_vector * width
        return Polygon(
            [geometry.cartesian_to_lon_lat(p, origin) for p in [p1, p2, p3]],
            color=color,
            alpha=0.7,
        )

    def redraw(self) -> None:
        """
        redraws the whole edge

        :return: None
        """
        if self.waypoint_plot is not None:
            self.waypoint_plot.remove()
            self.waypoint_plot = None
        self.plot_object.remove()
        self.draw()

    def draw(self) -> None:
        """
        draws the edge

        :return: None
        """
        self.plot_object = draw_edge(self.edge, self.ax, self.latlon, self.origin)
        self.plot_object.ref = self
        self.highlight()

def draw_nodes(graph: rg.Graph, ax: Axes, latlon: bool, origin: np.ndarray) -> Node:
    """
    scatters nodes of a graph

    :param latlon:
    :param origin:
    :param graph:
    :param ax:
    :return: the node object
    """
    node_list = list(graph.nodes)
    node_points = np.array([node.get_point().get_array() for node in node_list])
    if latlon:
        node_points = geometry.cartesian_to_lon_lat(node_points.T, origin).T
    scatter_object = ax.scatter(
        node_points[:, 0],
        node_points[:, 1],
        picker=PICKER_SIZE,
        color=[STANDARD_COLOR] * len(node_list),
        s=SCATTER_SIZE,
    )
    scatter_object.ref = Node(scatter_object, node_list, ax, latlon, origin)
    return scatter_object.ref

def draw_lane(lane: rg.Lane, ax: Axes, latlon: bool, origin: np.ndarray) -> None:
    """
    draws center line of a single lane

    :param lane: graph lane to draw
    :param ax: ax object to draw lane on
    :param latlon: defines whether the nodes are projected in geographic coordinates
    :param origin: origin of the cartesian coordinate system
    :return: None
    """
    waypoints_x, waypoints_y = [], []
    for waypoint in lane.waypoints:
        if latlon:
            assert origin is not None
            point_in_lat_lon = geometry.cartesian_to_lon_lat(waypoint, origin)
            lon, lat = point_in_lat_lon[0], point_in_lat_lon[1]
            waypoints_x.append(lon)
            waypoints_y.append(lat)
        else:
            waypoints_x.append(waypoint[0])
            waypoints_y.append(waypoint[1])
    ax.plot(waypoints_x, waypoints_y, color=STANDARD_COLOR, linewidth=LINE_WIDTH)
    # draw_lane_end_points(lane, ax, latlon, origin)
    return


def draw_all_lane_end_points(
    graph: rg.Graph, ax: Axes, latlon: bool, origin: np.ndarray
) -> Tuple[Collection, Collection, List[rg.Lane]]:
    """
    draws all lanes and end points of a graph

    :param graph: graph to draw from
    :param ax: axes to draw on
    :param latlon: defines whether the nodes are projected in geographic coordinates
    :param origin: origin of the cartesian coordinate system
    :return: Tuple: 1.start points of lanes, 2.end points of lanes, 3.lanes
    """

    def get_lane_end_points(lane: rg.Lane):
        point1 = lane.waypoints[0]
        point2 = lane.waypoints[-1]
        if latlon:
            point1 = geometry.cartesian_to_lon_lat(point1, origin)
            point2 = geometry.cartesian_to_lon_lat(point2, origin)
        return point1, point2

    points_at_start = []
    points_at_end = []
    lane_list = [lane for edge in graph.edges for lane in edge.lanes]
    for lane in lane_list:
        p1, p2 = get_lane_end_points(lane)
        points_at_start.append(p1)
        points_at_end.append(p2)

    points_at_start = np.array(points_at_start)
    points_at_end = np.array(points_at_end)

    sc1 = ax.scatter(
        points_at_start[:, 0],
        points_at_start[:, 1],
        color=STANDARD_COLOR,
        s=SCATTER_SIZE,
    )
    sc2 = ax.scatter(
        points_at_end[:, 0], points_at_end[:, 1], color=STANDARD_COLOR, s=SCATTER_SIZE
    )
    return sc1, sc2, lane_list

def draw_lanes(graph: rg.Graph, links: bool, ax: Axes, origin: np.ndarray) -> None:
    """
    draws center line of lanes in graph

    :param graph: graph to draw from
    :param links: true of lane-links should be drawn
    :param ax: axes to draw on
    :param origin: origin of the cartesian coordinate system
    :return: None
    """
    for edge in graph.edges:
        for lane in edge.lanes:
            draw_lane(lane, ax, True, origin)
    if links:
        for lane in graph.lanelinks:
            draw_lane(lane, ax, True, origin)
    return

def draw_single_arrow(
    lane: rg.Lane,
    last_point: np.ndarray,
    successor: rg.Lane,
    latlon: bool,
    origin: np.ndarray,
    ax: Axes,
    width: float,
    head_width: float,
    head_length: float,
) -> FancyArrow:
    """
    draw an arrow that represents the link between two lanes

    :param lane: predecessor lane
    :param last_point: last point of predecessor lane
    :param successor: successor lane
    :param latlon: defines whether the nodes are projected in geographic coordinates
    :param origin: origin of the cartesian coordinate system
    :param ax: axes to draw on
    :param width: width of the arrow line
    :param head_width: width of the arrow head
    :param head_length: length of the arrow head
    :return: the arrow, with plot object added to arrow.ref
    """
    first_point = successor.waypoints[0]
    if latlon:
        first_point = geometry.cartesian_to_lon_lat(first_point, origin)
    x = last_point[0]
    y = last_point[1]
    dx = first_point[0] - last_point[0]
    dy = first_point[1] - last_point[1]
    arrow = ax.arrow(
        x,
        y,
        dx,
        dy,
        picker=PICKER_SIZE,
        head_width=head_width,
        head_length=head_length,
        width=width,
        length_includes_head=True,
    )
    arrow.ref = Link(arrow, lane, successor)
    return arrow

def get_arrow_size(latlon: bool) -> Tuple[float, float, float]:
    """
    gets the necessary parameters for an arrow

    :param latlon: defines whether the nodes are projected in geographic coordinates
    :return: tuple of sizes of arrow
    """
    if latlon:
        head_width = 1e-5
        head_length = 2e-5
        width = 1e-7
        # TODO find better values for arrow size
        # print(head_width, head_length)
    else:
        head_width = 2
        head_length = 4
        width = 1e-3
    return width, head_width, head_length

def draw_lane_links(graph: rg.Graph, ax: Axes, latlon: bool, origin: np.ndarray):
    """
    draws the links between lanes as arrows
    these arrows can bew picked

    :param graph: the graph containing the lanes
    :param ax: axes to draw on
    :param latlon: defines whether the nodes are projected in geographic coordinates
    :param origin: origin of the cartesian coordinate system
    :return:
    """
    width, head_width, head_length = get_arrow_size(latlon)
    for edge in graph.edges:
        for lane in edge.lanes:
            last_point = lane.waypoints[-1]
            if latlon:
                last_point = geometry.cartesian_to_lon_lat(last_point, origin)
            for successor in lane.successors:
                draw_single_arrow(
                    lane,
                    last_point,
                    successor,
                    latlon,
                    origin,
                    ax,
                    width,
                    head_width,
                    head_length,
                )
    ax.figure.canvas.draw()
    return

def draw_edge(
    edge: rg.GraphEdge, ax: Axes, latlon: bool, origin: np.ndarray, color=STANDARD_COLOR
) -> Line2D:
    """
    draws an edge with desired projection

    :param edge: edge to draw
    :param ax: axes to draw on
    :param latlon: True if plot shall use geographic coordinate system
    :param origin: geographic coordinates of the origin of the cartesian coordinate system
    :param color: color to draw
    :return: line object of edges center line
    """
    waypoints = geometry.points_to_array(edge.waypoints)
    if latlon:
        waypoints = geometry.cartesian_to_lon_lat(waypoints.T, origin).T
    line = ax.plot(
        waypoints[:, 0],
        waypoints[:, 1],
        picker=PICKER_SIZE,
        color=color,
        linewidth=LINE_WIDTH,
    )[0]
    return line

def draw_edges(
    graph: rg.Graph, ax: Axes, latlon: bool, origin: np.ndarray, node_plot: Node
) -> Tuple[List[Line2D], Dict[rg.GraphNode, Set[Edge]]]:
    """
    draws all edges of a graph

    :param graph: graph containing edges
    :param ax: axes to draw on
    :param latlon: True if plot shall use geographic coordinate system
    :param origin: geographic coordinates of the origin of the cartesian coordinate system
    :param node_plot: plot of nodes
    :return: tuple: 1.lines, 2.map from graph nodes to adjacent edge plot objects
    """
    lines = []
    edge_sets_for_nodes = {node: set() for node in node_plot.node_list}
    # node_indices = {node: index for index, node in enumerate(node_plot.node_list)}
    for edge in graph.edges:
        line = draw_edge(edge, ax, latlon, origin)
        line.ref = Edge(line, edge, graph, latlon, ax, origin)
        lines.append(line)
        edge_sets_for_nodes[edge.node1].add(line.ref)
        edge_sets_for_nodes[edge.node2].add(line.ref)
    return lines, edge_sets_for_nodes

def draw_point(
    position: np.ndarray, origin: np.ndarray, ax: Axes, latlon: bool
) -> PointList:
    """
    draws a single point and returns a PointList containing it

    :param position: in cartesian coordinates
    :param origin: geographic coordinates of the origin of the cartesian coordinate system
    :param ax: axes to draw on
    :param latlon: True if plot shall use geographic coordinate system
    :return: list of point
    """
    if latlon:
        position = geometry.cartesian_to_lon_lat(position, origin)
    plot_object = ax.scatter(
        position[0],
        position[1],
        color=HIGHLIGHT_COLOR,
        picker=PICKER_SIZE,
        s=SCATTER_SIZE,
    )
    return PointList(plot_object, 1)
