"""
This module provides the infrastructure for actions performed by the user in the GUI.
Each Action can be reverted by an undo operation.
"""
import copy
from abc import ABC, abstractmethod
from threading import Lock
from typing import Callable, Tuple, Optional, List, Set, Dict

import numpy as np
from matplotlib.axes import Axes
from matplotlib.lines import Line2D

from crdesigner.map_conversion.osm2cr import config
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations import road_graph as rg
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations.road_graph import Lane
from crdesigner.input_output.gui.osm_gui_modules import plots_interactive as iplot
from crdesigner.map_conversion.osm2cr.converter_modules.utility import geometry
from crdesigner.map_conversion.osm2cr.converter_modules.utility.idgenerator import get_id


class Action(ABC):
    """
    an action modifies the graph structure and updates the interactive objects in the gui
    it is important, that an action always restores the exact same state of the graph and gui after undo()
    """

    @abstractmethod
    def __init__(self):
        self.done = False

    @abstractmethod
    def undo(self):
        assert self.done
        self.done = False

    @abstractmethod
    def do(self):
        assert not self.done
        self.done = True


class LinkDeletion(Action):
    """
    deletes a link between two lanes
    """

    def __init__(
        self,
        from_lane: Lane,
        to_lane: Lane,
        ax: Axes,
        origin: np.ndarray,
        link_object: iplot.Link,
    ):
        """

        :param from_lane: the predecessor lane
        :param to_lane: the successor lane
        :param ax: the axes of the plot
        :param origin: the coordinates of the origin of the coordinate system
        :param link_object: the link plot object
        """
        self.from_lane = from_lane
        self.to_lane = to_lane
        self.ax = ax
        self.origin = origin
        self.link_object = link_object
        super().__init__()

    def undo(self):
        connect_lanes(self.from_lane, self.to_lane)
        self.ax.add_patch(self.link_object.plot_object)
        self.ax.figure.canvas.draw()
        super().undo()
        print("LinkDeletion.undo()")

    def do(self):
        self.link_object.unhighlight()
        remove_link(self.link_object, self.ax)
        super().do()
        print("LinkDeletion.do()")


class LinkCreation(Action):
    """
    creates a link between two lanes
    """

    def __init__(self, from_lane: Lane, to_lane: Lane, ax: Axes, origin: np.ndarray):
        """

        :param from_lane: the predecessor lane
        :param to_lane: the successor lane
        :param ax: the axes of the plot
        :param origin: the coordinates of the origin of the coordinate system
        """
        self.from_lane = from_lane
        self.to_lane = to_lane
        self.ax = ax
        self.origin = origin
        self.link_object = None
        super().__init__()

    def undo(self):
        super().undo()
        remove_link(self.link_object, self.ax)
        print("LinkCreation.undo()")

    def do(self):
        connect_lanes(self.from_lane, self.to_lane)
        arrow = create_lane_link_arrow(
            self.from_lane, self.to_lane, self.ax, self.origin
        )
        self.link_object = arrow.ref
        super().do()
        print("LinkCreation.do()")


class EdgeWaypointDeletion(Action):
    """
    deletes a waypoint of an edge
    """

    def __init__(
        self,
        edge: iplot.Edge,
        index: int,
        ax: Axes,
        origin: np.ndarray,
        edge_picker: Callable[[iplot.Edge], None],
    ):
        """

        :param edge: the edge on which the waypoint is
        :param index: the index of the waypoint which is deleted
        :param ax: the axes of the plot
        :param origin: the coordinates of the origin of the coordinate system
        :param edge_picker: a function which selects the edge in the gui
        """
        # print(edge, index, ax, origin)
        self.edge = edge.edge
        self.edge_plot = edge
        self.index = index
        self.ax = ax
        self.origin = origin
        self.deleted_waypoint = self.edge.waypoints[index]
        self.edge_picker = edge_picker
        assert 0 < index < len(self.edge.waypoints) - 1
        super().__init__()

    def undo(self):
        super().undo()
        self.edge_picker(self.edge_plot)
        self.edge.waypoints = (
            self.edge.waypoints[: self.index]
            + [self.deleted_waypoint]
            + self.edge.waypoints[self.index :]
        )
        self.edge_plot.redraw()
        self.ax.figure.canvas.draw()

    def do(self):
        self.edge.waypoints = (
            self.edge.waypoints[: self.index] + self.edge.waypoints[self.index + 1 :]
        )
        self.edge_plot.redraw()
        self.ax.figure.canvas.draw()
        super().do()


class EdgeDeletion(Action):
    """
    deletes an edge
    """

    def __init__(
        self,
        edge: iplot.Edge,
        ax: Axes,
        graph: rg.Graph,
        edge_picker: Callable[[iplot.Edge], None],
        edge_sets_for_nodes: Dict[rg.GraphNode, Set[iplot.Edge]],
    ):
        """

        :param edge: the edge to delete
        :param ax: the axes of the plot
        :param graph: the graph on which the gui operates
        :param edge_picker: a function which selects the edge in the gui
        :param edge_sets_for_nodes: a dict which links the plot objects of all edges connected to a node to the node
        """
        super().__init__()
        self.edge_plot: iplot.Edge = edge
        self.ax = ax
        self.graph = graph
        self.edge_picker = edge_picker
        self.edge_sets_for_nodes: Dict[
            rg.GraphNode, Set[iplot.Edge]
        ] = edge_sets_for_nodes

    def undo(self):
        super().undo()
        self.edge_picker(self.edge_plot)
        self.graph.add_edge(self.edge_plot.edge)
        edge = self.edge_plot.edge
        self.edge_sets_for_nodes[edge.node1].add(self.edge_plot)
        self.edge_sets_for_nodes[edge.node2].add(self.edge_plot)
        self.edge_plot.draw()
        self.ax.figure.canvas.draw()

    def do(self):
        self.edge_plot.remove()
        edge = self.edge_plot.edge
        self.edge_sets_for_nodes[edge.node1].remove(self.edge_plot)
        self.edge_sets_for_nodes[edge.node2].remove(self.edge_plot)
        self.ax.figure.canvas.draw()
        super().do()


class EdgeWaypointMove(Action):
    """
    moves a waypoint of an edge to another position
    """

    def __init__(
        self,
        edge: iplot.Edge,
        ax: Axes,
        index: int,
        origin: np.ndarray,
        position: np.ndarray,
        edge_picker: Callable[[iplot.Edge], None],
        waypoint_picker: Callable[[Tuple[iplot.Edge, int]], None],
    ):
        """

        :param edge: the edge, the waypoint belongs to
        :param ax: the axes of the plot
        :param index: the index of the waypoint in the edge
        :param origin: the coordinates of the origin of the coordinate system
        :param position: the new position of the waypoint
        :param edge_picker: a function which selects the edge in the gui
        :param waypoint_picker: a function which selects the waypoint int the gui
        """
        super().__init__()
        self.edge: iplot.Edge = edge
        self.ax: Axes = ax
        self.index: int = index
        self.origin: np.ndarray = origin
        self.position: np.ndarray = position
        self.original_position: np.ndarray = edge.edge.waypoints[index].get_array()
        self.edge_picker: Callable[[iplot.Edge], None] = edge_picker
        self.waypoint_picker = waypoint_picker

    def undo(self):
        super().undo()
        self.edge_picker(self.edge)
        point = self.edge.edge.waypoints[self.index]
        point.set_position(self.original_position)
        self.edge.redraw()
        self.waypoint_picker((self.edge, self.index))
        self.ax.figure.canvas.draw()

    def do(self):
        point = self.edge.edge.waypoints[self.index]
        new_position = geometry.lon_lat_to_cartesian(self.position, self.origin)
        point.set_position(new_position)
        self.edge.redraw()
        self.waypoint_picker((self.edge, self.index))
        self.ax.figure.canvas.draw()
        super().do()


class NodeDeletion(Action):
    """
    deletes a Node in the graph
    """

    def __init__(
        self,
        node_index: int,
        graph: rg.Graph,
        ax: Axes,
        origin: np.ndarray,
        node_plot: iplot.Node,
        node_setter: Callable[[iplot.Node], None],
        node_picker: Callable[[Optional[int]], None],
    ):
        """

        :param node_index: index of the node in the gui list of nodes
        :param graph: the graph on which the gui operates
        :param ax: the axes of the plot
        :param origin: the coordinates of the origin of the coordinate system
        :param node_plot: the plot object of the nodes
        :param node_setter: a function to set the plot object of all nodes in the plot
        :param node_picker: a function to select a node in the gui
        """
        super().__init__()
        self.node_index: int = node_index
        self.node = node_plot.node_list[node_index]
        self.graph = graph
        self.ax = ax
        self.origin = origin
        self.old_node_plot = node_plot
        self.node_setter = node_setter
        self.node_picker = node_picker
        self.new_node_plot: Optional[iplot.Node] = None

    def undo(self):
        super().undo()
        self.graph.nodes.add(self.node)
        self.node_setter(self.old_node_plot)
        self.node_picker(self.node_index)
        self.new_node_plot.plot_object.remove()
        self.ax.add_collection(self.old_node_plot.plot_object)
        self.old_node_plot.highlight_single_node(self.node_index)
        self.ax.figure.canvas.draw()

    def do(self):
        self.graph.delete_node(self.node)
        self.old_node_plot.plot_object.remove()
        self.new_node_plot = iplot.draw_nodes(self.graph, self.ax, True, self.origin)
        self.node_setter(self.new_node_plot)
        self.node_picker(None)
        self.ax.figure.canvas.draw()
        super().do()


class NodeMove(Action):
    """
    moves a node in the gui
    """

    def __init__(
        self,
        node_index: int,
        ax: Axes,
        origin: np.ndarray,
        position: np.ndarray,
        node_plot: iplot.Node,
        node_picker: Callable[[Optional[int]], None],
        edge_sets_for_nodes: Dict[rg.GraphNode, Set[iplot.Edge]],
    ):
        """

        :param node_index: index of the node in the gui list of nodes
        :param ax: the axes of the plot
        :param origin: the coordinates of the origin of the coordinate system
        :param position: the new position of the node
        :param node_plot: the plot object of the nodes
        :param node_picker: a function to select a node in the gui
        :param edge_sets_for_nodes: a dict which links the plot objects of all edges connected to a node to the node
        """
        super().__init__()
        self.origin: np.ndarray = origin
        self.node_index: int = node_index
        self.ax: Axes = ax
        self.new_position: np.ndarray = position
        self.node_plot: iplot.Node = node_plot
        self.node_picker: Callable[[Optional[int]], None] = node_picker
        self.edge_sets_for_nodes: Dict[
            rg.GraphNode, Set[iplot.Edge]
        ] = edge_sets_for_nodes

        self.node: rg.GraphNode = node_plot.node_list[node_index]
        self.original_postition: np.ndarray = self.node.get_cooridnates()

    def undo(self):
        super().undo()
        self.node.move_to(self.original_postition)
        self.node_picker(self.node_index)
        self.node_plot.highlight_single_node(self.node_index)
        self.node_plot.redraw()
        for edge in self.edge_sets_for_nodes[self.node]:
            edge.redraw()
            edge.unhighlight()
        self.ax.figure.canvas.draw()

    def do(self):
        new_position = geometry.lon_lat_to_cartesian(self.new_position, self.origin)
        self.node.move_to(new_position)
        self.node_plot.redraw()
        for edge in self.edge_sets_for_nodes[self.node]:
            edge.redraw()
            edge.unhighlight()
        self.ax.figure.canvas.draw()
        super().do()


class EdgeWaypointAddition(Action):
    """
    adds a way point to an edge
    """

    def __init__(
        self,
        edge: iplot.Edge,
        index: int,
        edge_picker: Callable[[iplot.Edge], None],
        waypoint_picker: Callable[[Optional[Tuple[iplot.Edge, int]]], None],
        ax: Axes,
        origin: np.ndarray,
    ):
        """

        :param edge: the edge of the way point
        :param index: the index of the way point in the edge
        :param edge_picker: a function to select a node in the gui
        :param waypoint_picker: a function which selects the waypoint int the gui
        :param ax: the axes of the plot
        :param origin: the coordinates of the origin of the coordinate system
        """
        super().__init__()
        self.edge: iplot.Edge = edge
        # the new waypoint cannot be the starting or end point, and should be after the selected point
        self.index: int = min(max(1, index + 1), len(edge.edge.waypoints))
        self.edge_picker: Callable[[iplot.Edge], None] = edge_picker
        self.waypoint_picker: Callable[
            [Optional[Tuple[iplot.Edge, int]]], None
        ] = waypoint_picker
        self.ax: Axes = ax
        self.origin: np.ndarray = origin

    def undo(self):
        super().undo()
        waypoints = self.edge.edge.waypoints
        self.edge.edge.waypoints = waypoints[: self.index] + waypoints[self.index + 1 :]
        self.edge.redraw()
        if self.edge.waypoint_plot is not None:
            self.edge.waypoint_plot.unhighlight()
        self.waypoint_picker(None)
        self.edge_picker(self.edge)
        self.edge.highlight()
        self.ax.figure.canvas.draw()

    def do(self):
        new_pos = (
            self.edge.edge.waypoints[self.index - 1].get_array()
            + self.edge.edge.waypoints[self.index].get_array()
        ) / 2
        x, y = new_pos[0], new_pos[1]
        new_point = geometry.Point(get_id(), x, y)
        self.edge.edge.waypoints.insert(self.index, new_point)
        self.edge_picker(self.edge)
        self.edge.redraw()
        self.waypoint_picker((self.edge, self.index))
        self.ax.figure.canvas.draw()
        super().do()


class EdgeSplit(Action):
    """
    splits an edge into two and creates a new node between them
    """

    def __init__(
        self,
        split_index: int,
        edge_plot: iplot.Edge,
        origin: np.ndarray,
        ax: Axes,
        node_plot: iplot.Node,
        graph: rg.Graph,
        gui_edge_plot: List[Line2D],
        edge_sets_for_nodes,
        node_setter: Callable[[iplot.Node], None],
        node_picker: Callable[[Optional[int]], None],
        edge_picker: Callable[[Optional[iplot.Edge]], None],
    ):
        """

        :param split_index: the index of the way point at which the edge is split
        :param edge_plot: the plot object of the edge
        :param origin: the coordinates of the origin of the coordinate system
        :param ax: the axes of the plot
        :param node_plot: the plot object of the nodes
        :param graph: the graph on which the gui operates
        :param gui_edge_plot: the plot object of the edges
        :param edge_sets_for_nodes: a dict which links the plot objects of all edges connected to a node to the node
        :param node_setter: a function to set the plot object of all nodes in the plot
        :param node_picker: a function to select a node in the gui
        :param edge_picker: a function which selects the edge in the gui
        """
        super().__init__()
        self.split_index: int = split_index
        self.edge_plot: iplot.Edge = edge_plot
        self.origin: np.ndarray = origin
        self.ax: Axes = ax
        self.node_plot = node_plot
        self.graph = graph
        self.gui_edge_plot = gui_edge_plot
        self.edge_sets_for_nodes = edge_sets_for_nodes
        self.node_setter = node_setter
        self.node_picker: Callable[[Optional[int]], None] = node_picker
        self.edge_picker: Callable[[Optional[iplot.Edge]], None] = edge_picker

        self.node1: rg.GraphNode = edge_plot.edge.node1
        self.node2: rg.GraphNode = edge_plot.edge.node2
        self.own_actions: ActionHistory = ActionHistory()
        self.intermediate_node_plot: Optional[iplot.Node] = node_plot

    def undo(self):
        while not self.own_actions.empty:
            self.own_actions.undo()
        self.node_setter(self.intermediate_node_plot)
        self.ax.figure.canvas.draw()
        super().undo()

    def do(self):
        middle_waypoint = self.edge_plot.edge.waypoints[self.split_index]
        middle_node = rg.GraphNode(
            get_id(), middle_waypoint.x, middle_waypoint.y, set()
        )
        waypoints1 = self.edge_plot.edge.waypoints[: self.split_index + 1]
        waypoints1 = [point.get_array() for point in waypoints1]
        self.own_actions.add(
            EdgeDeletion(
                self.edge_plot,
                self.ax,
                self.graph,
                self.edge_picker,
                self.edge_sets_for_nodes,
            )
        )
        self.own_actions.add(
            EdgeCreation(
                waypoints1,
                self.node1,
                middle_node,
                self.graph,
                self.intermediate_node_plot,
                self.gui_edge_plot,
                self.edge_sets_for_nodes,
                self.ax,
                self.origin,
                self.intermediate_node_setter,
                self.node_picker,
                self.edge_picker,
            )
        )
        waypoints2 = self.edge_plot.edge.waypoints[self.split_index :]
        waypoints2 = [point.get_array() for point in waypoints2]
        self.own_actions.add(
            EdgeCreation(
                waypoints2,
                middle_node,
                self.node2,
                self.graph,
                self.intermediate_node_plot,
                self.gui_edge_plot,
                self.edge_sets_for_nodes,
                self.ax,
                self.origin,
                self.intermediate_node_setter,
                self.node_picker,
                self.edge_picker,
            )
        )
        middle_node_index = self.intermediate_node_plot.node_list.index(middle_node)
        self.node_setter(self.intermediate_node_plot)
        self.node_picker(middle_node_index)
        self.intermediate_node_plot.highlight_single_node(middle_node_index)
        self.ax.figure.canvas.draw()
        super().do()

    def intermediate_node_setter(self, node_plot: iplot.Node):
        # this action only modifies the intermediate node plot within it's intermediate steps
        self.intermediate_node_plot = node_plot


class EdgeCreation(Action):
    """
    creates a new edge
    """

    def __init__(
        self,
        waypoints: List[np.ndarray],
        node1: rg.GraphNode,
        node2: rg.GraphNode,
        graph: rg.Graph,
        node_plot: iplot.Node,
        edge_plot: List[Line2D],
        edge_sets_for_nodes: Dict[rg.GraphNode, Set[iplot.Edge]],
        ax: Axes,
        origin: np.ndarray,
        node_setter: Callable[[iplot.Node], None],
        node_picker: Callable[[Optional[int]], None],
        edge_picker: Callable[[Optional[iplot.Edge]], None],
    ):
        """

        :param waypoints: the waypoints of the new edge
        :param node1: the node the new edge starts at
        :param node2: the node the new edge ends at
        :param graph: the graph on which the gui operates
        :param node_plot: the plot of the nodes
        :param edge_plot: the plot of the edges
        :param edge_sets_for_nodes: a dict which links the plot objects of all edges connected to a node to the node
        :param ax: the axes of the plot
        :param origin: the coordinates of the origin of the coordinate system
        :param node_setter: a function to set the plot object of all nodes in the plot
        :param node_picker: a function to select a node in the gui
        :param edge_picker: a function which selects the edge in the gui
        """
        super().__init__()
        self.waypoints = waypoints
        self.node1 = node1
        self.node2 = node2
        self.graph = graph
        self.edge: Optional[rg.GraphEdge] = None
        self.node_plot_old = node_plot
        self.node_plot_new: Optional[iplot.Node] = None
        self.graph_edge_plot = edge_plot
        self.edge_sets_for_nodes = edge_sets_for_nodes
        self.ax = ax
        self.origin = origin
        self.node_setter = node_setter
        self.interactive_edge: Optional[iplot.Edge] = None
        self.node_picker: Callable[[Optional[int]], None] = node_picker
        self.edge_picker: Callable[[Optional[iplot.Edge]], None] = edge_picker

    def undo(self):
        super().undo()
        self.interactive_edge.remove()
        self.edge_sets_for_nodes[self.node1].remove(self.interactive_edge)
        self.edge_sets_for_nodes[self.node2].remove(self.interactive_edge)
        if self.node2 not in self.node_plot_old.node_list:
            self.graph.delete_node(self.node2)
        self.node_plot_new.plot_object.remove()
        self.ax.add_collection(self.node_plot_old.plot_object)
        self.node_setter(self.node_plot_old)
        self.node_picker(self.node_plot_old.node_list.index(self.node1))
        self.ax.figure.canvas.draw()

    def do(self):
        if self.node1 not in self.graph.nodes:
            self.graph.nodes.add(self.node1)
        if self.node2 not in self.graph.nodes:
            self.graph.nodes.add(self.node2)

        waypoints = [
            geometry.Point(get_id(), point[0], point[1]) for point in self.waypoints
        ]
        lane_info = 2, 1, 1, False, None, None, None
        assumptions = False, False, False
        self.edge = rg.GraphEdge(
            get_id(),
            self.node1,
            self.node2,
            waypoints,
            lane_info,
            assumptions,
            50,
            "primary",
        )
        self.edge.generate_lanes()
        self.graph.edges.add(self.edge)
        self.node1.edges.add(self.edge)
        self.node2.edges.add(self.edge)

        edge_plot = iplot.draw_edge(self.edge, self.ax, True, self.origin)
        interactive_edge = iplot.Edge(
            edge_plot, self.edge, self.graph, True, self.ax, self.origin
        )
        self.interactive_edge = interactive_edge
        edge_plot.ref = interactive_edge
        if self.node1 not in self.edge_sets_for_nodes:
            self.edge_sets_for_nodes[self.node1] = set()
        if self.node2 not in self.edge_sets_for_nodes:
            self.edge_sets_for_nodes[self.node2] = set()
        self.edge_sets_for_nodes[self.node1].add(interactive_edge)
        self.edge_sets_for_nodes[self.node2].add(interactive_edge)
        self.graph_edge_plot.append(edge_plot)

        self.node_plot_old.plot_object.remove()
        new_node_plot = iplot.draw_nodes(self.graph, self.ax, True, self.origin)
        self.node_plot_new = new_node_plot
        self.node_setter(new_node_plot)
        self.edge_picker(interactive_edge)
        interactive_edge.highlight()
        self.ax.figure.canvas.draw()
        super().do()


class LaneWidthEditing(Action):
    """
    sets the width of lanes of an edge new
    """

    def __init__(
        self,
        graph: rg.Graph,
        unhighlight_fun: Callable,
        ax: Axes,
        original_lanewidth_config: Dict[str, float],
    ):
        """

        :param graph: the graph on which the gui operates
        :param unhighlight_fun: a function to unhighlight the whole plot
        :param ax: the axes of the plot
        :param original_lanewidth_config:
        """
        super().__init__()
        self.graph: rg.Graph = graph
        self.unhighlight_fun = unhighlight_fun
        self.ax = ax
        self.original_lanewidth_config = original_lanewidth_config
        self.original_lanewidths: Dict[rg.GraphEdge, int] = {}
        for edge in graph.edges:
            self.original_lanewidths[edge] = edge.lanewidth
        self.new_lane_widths = copy.deepcopy(config.LANEWIDTHS)

    def undo(self):
        super().undo()
        self.unhighlight_fun()
        for edge in self.graph.edges:
            edge.lanewidth = self.original_lanewidths[edge]
            for lane in edge.lanes:
                lane.width1 = lane.width2 = self.original_lanewidths[edge]
        self.ax.figure.canvas.draw()
        config.LANEWIDTHS = self.original_lanewidth_config

    def do(self):
        self.unhighlight_fun()
        for edge in self.graph.edges:
            edge.lanewidth = self.new_lane_widths[edge.roadtype]
            for lane in edge.lanes:
                lane.width1 = lane.width2 = self.new_lane_widths[edge.roadtype]
        self.ax.figure.canvas.draw()
        config.LANEWIDTHS = self.new_lane_widths
        super().do()


def connect_lanes(from_lane: Lane, to_lane: Lane) -> None:
    """
    connects two lanes, by setting predecessors and successors respectively

    :param from_lane: the predecessor lane
    :param to_lane: the successor lane
    :return: None
    """
    print("to in from: {}".format(to_lane in from_lane.successors))
    print("from in to: {}".format(from_lane in to_lane.predecessors))
    assert (to_lane in from_lane.successors) == (from_lane in to_lane.predecessors)
    if to_lane in from_lane.successors:
        print("lanes are already connected")
        return
    from_lane.successors.add(to_lane)
    to_lane.predecessors.add(from_lane)


def create_lane_link_arrow(
    from_lane: Lane, to_lane: Lane, ax: Axes, origin: np.ndarray
) -> None:
    """
    creates an arrow between two lanes and draws it on ax

    :param from_lane: the predecessor lane
    :param to_lane: the successor lane
    :param ax: the axes of the plot
    :param origin: the coordinates of the origin of the coordinate system
    :return: None
    """
    width, head_width, head_length = iplot.get_arrow_size(True)
    last_point = from_lane.waypoints[-1]
    last_point = geometry.cartesian_to_lon_lat(last_point, origin)
    arrow = iplot.draw_single_arrow(
        from_lane, last_point, to_lane, True, origin, ax, width, head_width, head_length
    )
    ax.figure.canvas.draw()
    return arrow


def remove_link(link_object: iplot.Link, ax: Axes) -> None:
    """
    removes a link object from a plot and redraws plot

    :param link_object: the link to remove
    :param ax: the axes of the plot
    :return: None
    """
    link_object.remove()
    ax.figure.canvas.draw()


class ActionHistory:
    """
    a class to easily keep a reversible history of all performed actions
    """

    def __init__(self):
        self.actions = []
        self.reverted_actions = []
        self.lock = Lock()

    def __getstate__(self):
        state = self.__dict__.copy()
        del state["lock"]
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.lock = Lock()

    def add(self, action: Action) -> None:
        """
        executes the action and appends it to the history

        :param action: the action to add
        :return: None
        """
        self.lock.acquire()
        self.reverted_actions = []
        self.actions.append(action)
        action.do()
        self.lock.release()

    def undo(self) -> None:
        """
        undoes the last action in the history

        :return: None
        """
        self.lock.acquire()
        if len(self.actions) <= 0:
            print("no action to undo")
            self.lock.release()
            return
        action = self.actions[-1]
        action.undo()
        self.actions = self.actions[:-1]
        self.reverted_actions.append(action)
        self.lock.release()

    def redo(self) -> None:
        """
        redoes the last undone action

        :return: None
        """
        self.lock.acquire()
        if len(self.reverted_actions) <= 0:
            print("no action to redo")
            self.lock.release()
            return
        action = self.reverted_actions[-1]
        action.do()
        self.actions.append(action)
        self.reverted_actions = self.reverted_actions[:-1]
        self.lock.release()

    @property
    def empty(self) -> bool:
        return len(self.actions) == 0

    @property
    def redo_empty(self) -> bool:
        return len(self.reverted_actions) == 0
