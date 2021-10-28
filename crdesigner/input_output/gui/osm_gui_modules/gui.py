"""
This module contains the editors of edges and lane links in matplotlib
These GUIs can be used with any embedding that can contain a matplotlib canvas
"""
import copy
import datetime
import os
import pickle
from abc import ABC, abstractmethod
from tkinter import Tk
from tkinter.filedialog import askopenfilename, asksaveasfilename
from typing import Optional, List, Tuple, Set, Dict, Callable

import cartopy.crs as crs
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from matplotlib.backend_bases import MouseEvent, PickEvent, KeyEvent
from matplotlib.collections import Collection
from matplotlib.lines import Line2D
from matplotlib.backends.backend_agg import FigureCanvasAgg

from crdesigner.map_conversion.osm2cr import config
import crdesigner.map_conversion.osm2cr.converter_modules.graph_operations.road_graph as rg
from crdesigner.input_output.gui.osm_gui_modules import aerial_data, actions, plots_interactive as iplot
from crdesigner.input_output.gui.osm_gui_modules.settings import EditLaneWidth
from crdesigner.map_conversion.osm2cr.converter_modules.utility import geometry
from crdesigner.map_conversion.osm2cr.converter_modules.utility.idgenerator import get_id


def check_dir(directory: str) -> None:
    """
    checks if the directory exists, if not creates directory

    :param directory:
    :return: None
    """
    if not os.path.exists(directory):
        os.makedirs(directory)


class GUI(ABC):
    """
    abstract class for a GUI
    """

    def __init__(self, graph: rg.Graph, reloader: Optional[Callable[[], None]]):
        """

        :param graph: the graph to edit
        :param reloader: a method to reload the GUI in a new embedding
        """
        # setup figure and axes
        self.fig, self.ax = plt.subplots()  # constrained_layout=True)
        self.projection = crs.Mercator()
        self.ax = plt.axes(projection=self.projection)
        plt.axis("on")
        self.origin: np.ndarray = np.array(graph.center_point)
        self.graph: rg.Graph = graph

        self.restart: bool = False
        self.new_gui: Optional[GUI] = None
        self.reloader: Optional[Callable[[], None]] = reloader

        # plot aerial image
        lat1, lon1, lat2, lon2 = graph.bounds
        if config.AERIAL_IMAGES:
            image, extents = aerial_data.get_aerial_image(
                lat1, lon1, lat2, lon2, zoom=config.ZOOM_LEVEL
            )
            iplot.plot_aerial_image(image, extents, self.ax, self.projection)

        # setup bounds of plot
        self.ax.set_xlim(lon1, lon2)
        self.ax.set_ylim(lat2, lat1)

        # setup action historys
        self.action_history: actions.ActionHistory = actions.ActionHistory()

        # set the title
        self.ax.set_title("")

        # draw necessary for tight layout: see issue #1207 at cartopy github
        self.fig.canvas.draw()
        self.fig.tight_layout()

    def plot_image(self, image: Image, image_extent: List[float]) -> None:
        """
        plots an image in the current plot

        :param image: image to plot
        :param image_extent: coordinates of the image
        :return: None
        """
        self.ax.imshow(
            image, origin="upper", extent=image_extent, transform=self.projection
        )
        return

    def save_state(self, filename: str) -> None:
        """
        saves the current gui object to disk

        :param filename: the filename used to save
        :return: None
        """
        # simply save gui object
        check_dir(os.path.dirname(filename))
        # the reloader must not be pickled
        tmp = self.reloader
        self.reloader = None
        with open(filename, "wb") as fd:
            pickle.dump(self, fd, protocol=pickle.HIGHEST_PROTOCOL)
        self.reloader = tmp

    def load_state(self, filename: str) -> None:
        """
        loads a state from disk and sets it as an attribute
        the current gui closes and has to be restarted as self.new_gui to make it editable

        :param filename: the filname used to save
        :return: None
        """
        old_fig = self.fig
        if os.path.exists(filename):
            fd = open(filename, "rb")
            try:
                new_gui = pickle.load(fd)
            except TypeError:
                print_grey("file cannot be loaded")
                return
            if type(new_gui) != type(self):
                print_grey("file is of wrong type")
                return
            # notify window to reload plot
            self.restart = True
            self.new_gui = new_gui
            if self.reloader is not None:
                self.new_gui.reloader = self.reloader
                self.reloader()
            else:
                plt.close(old_fig)
        else:
            print_grey("no file loaded")

    @abstractmethod
    def setup_event_listeners(self, canvas):
        return


class LaneLinkGUI(GUI):
    """
    GUI that allows user to edit connections between individual lanes
    """

    def __init__(self, graph: rg.Graph, reloader: Optional[Callable[[], None]]):
        """

        :param graph: the graph to edit
        :param reloader: a method to reload the GUI in a new embedding
        """
        super().__init__(graph, reloader)

        # setup variables for previously picked objects
        self.last_picked: Optional[iplot.Link] = None
        self.from_lane: Optional[rg.Lane] = None

        # plot lanes and links with interactive start points
        iplot.draw_lanes(graph, False, self.ax, self.origin)
        iplot.draw_lane_links(graph, self.ax, True, self.origin)
        start_points, end_points, lanelist = iplot.draw_all_lane_end_points(
            graph, self.ax, True, self.origin
        )
        self.start_points: Collection = start_points
        self.end_points: Collection = end_points
        self.lanelist: List[rg.Lane] = lanelist

        self.setup_event_listeners(self.fig.canvas)

    def setup_event_listeners(self, canvas: FigureCanvasAgg) -> None:
        """
        connects all necessary event listeners

        :param canvas: canvas of the plot
        :return: None
        """
        plt.rcParams["keymap.save"] = ""
        canvas.mpl_connect("pick_event", self.on_pick)
        canvas.mpl_connect("key_press_event", self.on_key)
        canvas.mpl_connect("button_press_event", self.on_press)
        canvas.mpl_connect("button_release_event", self.on_release)

    def on_key(self, event: KeyEvent) -> None:
        """
        reads pressed keys and executes actions based on them:
        del: remove element

        :param event: key event
        :return: None
        """
        # print_grey(event.key)
        if event.key == u"delete":
            self.delete()
        elif event.key == "ctrl+z":
            self.undo()
        elif event.key == "ctrl+Z":
            self.redo()
        elif event.key == "ctrl+s":
            self.save()
        elif event.key == "ctrl+l":
            self.load()

    def delete(self) -> None:
        """
        called by the delete event
        it deletes the highlighted link

        :return: None
        """
        if self.last_picked is not None:
            print_grey("deleting highlighted object")
            del_action = actions.LinkDeletion(
                self.last_picked.from_lane,
                self.last_picked.to_lane,
                self.ax,
                self.origin,
                self.last_picked,
            )
            self.action_history.add(del_action)
            self.last_picked = None
        else:
            print_grey("no object to delete")

    def undo(self) -> None:
        """
        called by undo event
        undoes last operation

        :return: None
        """
        self.action_history.undo()

    def redo(self) -> None:
        """
        called by redo event
        redoes last undone operation

        :return: None
        """
        self.action_history.redo()

    def save(self) -> None:
        """
        save current state of the edit to disk
        this includes the action history which makes it necessary to save the whole plot

        :return: None
        """
        name = "link_save_{}.save".format(
            datetime.datetime.now().strftime("%y-%m-%d_%H-%M-%S")
        )
        check_dir("files/link_saves")
        Tk().withdraw()
        file = asksaveasfilename(
            initialdir="files/link_saves",
            initialfile=name,
            defaultextension=".save",
            filetypes=(("save file", "*.save"), ("All Files", "*.*")),
        )
        if file != "" and file is not None:
            self.save_state(file)

    def load(self) -> None:
        """
        load an old edit state from disk

        :return: None
        """
        Tk().withdraw()
        check_dir("files/link_saves")
        self.load_state(
            askopenfilename(
                initialdir="files/link_saves",
                filetypes=(("save files", "*.save"), ("all files", "*.*")),
            )
        )

    def on_press(self, event: MouseEvent) -> None:
        """
        handles the event, when a mouse button is pressed

        :param event: mouse event
        :return: None
        """
        if event.inaxes != self.ax:
            return
        contains, ind = self.end_points.contains(event)
        if contains:
            self.from_lane = self.lanelist[ind["ind"][0]]
            print_grey("pressed on end of a lane")

    def on_release(self, event: MouseEvent) -> None:
        """
        handles the event, when a mouse button is released

        :param event: mouse event
        :return: None
        """
        if not event.inaxes == self.ax:
            return
        contains, ind = self.start_points.contains(event)
        if contains:
            print_grey("released on start of a lane")
            if self.from_lane is not None:
                to_lane = self.lanelist[ind["ind"][0]]
                self.action_history.add(
                    actions.LinkCreation(self.from_lane, to_lane, self.ax, self.origin)
                )
        self.from_lane = None

    def on_pick(self, event: PickEvent) -> None:
        """
        reads picked elements and highlights it

        :param event: pick event
        :return: None
        """
        print_grey("object picked")
        if self.last_picked is not None:
            self.last_picked.unhighlight()
        this_artist = event.artist
        picked_object = this_artist
        picked_object.ref.highlight()
        self.last_picked = picked_object.ref
        self.ax.figure.canvas.draw()


class EdgeEditGUI(GUI):
    """
    GUI that allows the user to edit the course of edges, add new edges, delete edges and change all parameters of edges
    """

    def __init__(
        self,
        graph: rg.Graph,
        reloader: Optional[Callable[[], None]],
        pick_listener: Optional[Callable[[rg.GraphEdge], None]],
        movement_updater: Optional[Callable[[bool], None]],
    ):
        """

        :param graph: the graph to edit
        :param reloader: a method to reload the GUI in a new embedding
        :param pick_listener: a function given by an embedding the inform it about the currently picked edge
        :param movement_updater: a function that propagates the current state of movement to the embedding
        """
        super().__init__(graph, reloader)
        self.last_picked_edge: Optional[iplot.Edge] = None
        self.last_picked_node: Optional[int] = None
        self.last_picked_way_point: Optional[Tuple[iplot.Edge, int]] = None
        self.last_pressed_way_point: Optional[Tuple[iplot.Edge, int]] = None
        self.last_pressed_node: Optional[int] = None

        # plot edges with interactive nodes
        self.edges: List[Line2D]
        self.edge_sets_for_nodes: Dict[rg.GraphNode, Set[iplot.Edge]]
        self.node_plot: iplot.Node = iplot.draw_nodes(graph, self.ax, True, self.origin)
        self.edges, self.edge_sets_for_nodes = iplot.draw_edges(
            graph, self.ax, True, self.origin, self.node_plot
        )

        # placeholder for waypoints of picked edges
        self.edge_waypoints: Optional[iplot.PointList] = None

        # variable for the user to toggle movement of points
        self.move_objects: bool = False

        # variables for creating a new edge
        self.edge_create_mode: bool = False
        self.new_edge_waypoint_plots: Optional[List[iplot.Node]] = None
        self.new_edge_waypoints: Optional[List[np.ndarray]] = None
        self.new_edge_start_node: Optional[rg.GraphNode] = None

        # window to edit the width of lanes
        self.width_edit_window: Optional[EditLaneWidth] = None

        self.setup_event_listeners(self.fig.canvas)
        self.pick_listener = pick_listener

        # set movement updater for embedding
        self.update_movement: Callable[[bool], None] = movement_updater

    def setup_event_listeners(self, canvas):
        plt.rcParams["keymap.save"] = ""
        canvas.mpl_connect("pick_event", self.on_pick)
        canvas.mpl_connect("key_press_event", self.on_key)
        canvas.mpl_connect("button_press_event", self.on_press)
        canvas.mpl_connect("button_release_event", self.on_release)

    def redraw(self) -> None:
        """
        redraws all elements in the edit plot

        :return: None
        """
        for edge in self.edges:
            edge.ref.ax = self.ax
            edge.ref.draw()
            edge.ref.unhighlight()
        self.node_plot.ax = self.ax
        self.node_plot.draw()

    def unhighlight(self) -> None:
        """
        unhighlights the currently picked element

        :return: None
        """
        if self.last_picked_node is not None:
            self.node_plot.unhighlight()
            self.last_picked_node = None

        if self.last_picked_edge is not None:
            self.last_picked_edge.unhighlight()
            self.last_picked_edge = None
            if self.last_picked_way_point is not None:
                self.last_picked_way_point = None

        self.last_pressed_way_point = None
        self.last_pressed_node = None

    def pick_edge(self, edge: Optional[iplot.Edge]) -> None:
        """
        this callable can be used by actions to set the picked edge

        :param edge: edge plot object of picked edge
        :return: None
        """
        self.unhighlight()
        self.last_picked_edge = edge
        if self.pick_listener is not None:
            if edge is not None:
                self.pick_listener(edge.edge)
            else:
                self.pick_listener(None)
        if self.last_picked_edge is not None:
            self.edge_waypoints = self.last_picked_edge.waypoint_plot

    def pick_node(self, node_index: Optional[int]) -> None:
        """
        this callable can ve used by actions to set the picked node_index
        the node has to be highlighted by the caller manually

        :param node_index: the index of the node to pick
        :return: None
        """
        self.unhighlight()
        self.last_picked_node = node_index

    def save_state(self, filename: str) -> None:
        """
        saves the current state of the edit to disk

        :param filename: filename for file to save
        :return: None
        """
        tmp = self.pick_listener, self.update_movement
        self.pick_listener = self.update_movement = None
        super().save_state(filename)
        self.pick_listener, self.update_movement = tmp

    def pick_waypoint(self, waypoint: Optional[Tuple[iplot.Edge, int]]) -> None:
        """
        picks and highlights a waypoint
        the index of the waypoint is index of pointlist + 1

        :param waypoint: Tuple defining the waypoint: [edge plot object, index of the picked way point]
        :return: None
        """
        if waypoint is not None:
            assert (
                self.last_picked_edge is not None
            ), "picked a waypoint without a selected edge"
            edge, index = waypoint
            edge.redraw()
            edge.waypoint_plot.highlight_single_point(waypoint[1] - 1)
            self.edge_waypoints = edge.waypoint_plot
        self.last_picked_way_point = waypoint

    def set_nodes(self, node_plot: iplot.Node) -> None:
        """
        sets the node scatter and node list to the gui
        this method can be used by an action to modify the current nodes

        :param node_plot: plot of nodes
        :return: None
        """
        self.node_plot = node_plot

    def on_pick(self, event: PickEvent) -> None:
        """
        reads picked elements and highlights it

        :param event: the pick event
        :return: None
        """
        if self.edge_create_mode:
            print_grey("cannot pick while creating a new edge")
            return

        print_grey("object picked")
        object_type = type(event.artist.ref)

        if self.last_picked_node is not None:
            # old nodes are unhighlighted
            self.node_plot.unhighlight()
            self.last_picked_node = None

        if self.last_picked_way_point is not None:
            # old edge waypoint is unhighlighted
            self.last_picked_way_point[0].waypoint_plot.unhighlight()
            self.last_picked_way_point = None

        if self.last_picked_edge is not None and object_type != iplot.PointList:
            # if the picked object is not a point on the picked edge, we unhighlight it
            self.last_picked_edge.unhighlight()
            self.last_picked_edge = None

        if object_type == iplot.Node:
            # picked a node

            self.pick_edge(None)

            picked_object = event.artist
            node_index = event.ind[0]  # the warning at this line can be ignored
            self.last_picked_node = picked_object.ref.highlight_single_node(node_index)

        elif object_type == iplot.Edge:
            # picked an edge
            picked_object = event.artist
            picked_object.ref.highlight()

            # self.last_picked_edge = picked_object.ref
            self.pick_edge(picked_object.ref)

        elif object_type == iplot.PointList:
            # picked a waypoint of an edge
            point_index = event.ind[0]  # the warning at this line can be ignored
            # as the first and last waypoints are not displayed we need to add one from the index
            waypoint = (self.last_picked_edge, point_index + 1)
            self.pick_waypoint(waypoint)  # the warning at this line can be ignored

        else:
            print_grey("PICKED UNKNOWN OBJECT!")
        self.ax.figure.canvas.draw()

    def on_key(self, event: KeyEvent) -> None:
        """
        reads pressed keys and executes actions based on them:
        delete: remove element
        ctrl+z: undo last action
        ctrl+shift+z: redo last undone action
        ctrl+m: toggle movement of objects
        ctrl+n: create new waypoint on edge
        ctrl+s: save the current state of the edit to disk
        ctrl+l: load an edit state from the disk
        ctrl+d: dissect edge at picked waypoint
        ctrl+e: create new edge
        ctrl+w: edit width of lanes

        :param event: key event
        :return: None
        """
        # print_grey(event.key)
        if self.edge_create_mode:
            print_grey("cannot do that while creating new edge")
            return
        if event.key == u"delete":
            self.delete()
        elif event.key == "ctrl+z":
            self.undo()
        elif event.key == "ctrl+Z":
            self.redo()
        elif event.key == u"ctrl+m":
            self.move()
        elif event.key == u"ctrl+n":
            self.new_waypoint()
        elif event.key == u"ctrl+s":
            self.save()
        elif event.key == u"ctrl+l":
            self.load()
        elif event.key == u"ctrl+d":
            self.split()
        elif event.key == u"ctrl+e":
            self.create_edge()
        elif event.key == u"ctrl+w":
            self.edit_width()

    def edge_create_action(self, event: MouseEvent) -> None:
        """
        defines the behavior if  edge_creation_mode is True and the mouse is pressed
        in this mode, the user can create new edges by defining way points and the end node

        :param event: mouse event
        :return: None
        """
        assert self.new_edge_waypoint_plots is not None
        # waypoint for new edge will be set
        position = np.array([event.ydata, event.xdata])
        cartesian_pos = geometry.lon_lat_to_cartesian(position, self.origin)
        if event.button == 3:
            # add edge to graph
            contains, ind = self.node_plot.plot_object.contains(event)
            if contains:
                # new edge ends at an existing node
                ind = ind["ind"][0]
                node2 = self.node_plot.node_list[ind]
            else:
                # new edge ends at click position
                node2 = rg.GraphNode(
                    get_id(), cartesian_pos[0], cartesian_pos[1], set()
                )
            for point in self.new_edge_waypoint_plots:
                point.remove()
            waypoints = (
                [self.new_edge_start_node.get_cooridnates()]
                + self.new_edge_waypoints
                + [node2.get_cooridnates()]
            )
            self.action_history.add(
                actions.EdgeCreation(
                    waypoints,
                    self.new_edge_start_node,
                    node2,
                    self.graph,
                    self.node_plot,
                    self.edges,
                    self.edge_sets_for_nodes,
                    self.ax,
                    self.origin,
                    self.set_nodes,
                    self.pick_node,
                    self.pick_edge,
                )
            )
            self.edge_create_mode = False
            self.new_edge_waypoint_plots = None
            self.new_edge_waypoints = None
            self.new_edge_start_node = None
            print_grey("adding edge")
        elif event.button == 1:
            # add waypoint to new edge
            new_waypoint = iplot.draw_point(cartesian_pos, self.origin, self.ax, True)
            self.new_edge_waypoint_plots.append(new_waypoint)
            self.new_edge_waypoints.append(cartesian_pos)
            self.ax.figure.canvas.draw()
            print_grey("adding new way point")

    def on_press(self, event: MouseEvent) -> None:
        """
        handles the press event
        used to move objects

        :param event: mouse event
        :return: None
        """
        if event.inaxes != self.ax:
            return
        self.last_pressed_way_point = None
        self.last_pressed_node = None

        if self.edge_create_mode:
            self.edge_create_action(event)
            return

        if self.last_picked_node is not None:
            contains, ind = self.node_plot.plot_object.contains(event)
            if contains:
                ind = ind["ind"][0]
                self.last_pressed_node = ind
                print_grey("pressed on a node")

        if self.last_picked_edge is not None and self.edge_waypoints is not None:
            # assert self.edge_waypoints is not None, "waypoints of highligted edge are not registered in gui"
            contains, ind = self.edge_waypoints.plot_object.contains(event)
            if contains:
                ind = ind["ind"][0] + 1
                self.last_pressed_way_point = (self.last_picked_edge, ind)
                print_grey("pressed on an edge waypoint")

    def on_release(self, event: MouseEvent) -> None:
        """
        handles the release event
        used to move objects

        :param event: mouse event
        :return: None
        """
        if event.inaxes != self.ax:
            return
        if (
            self.last_pressed_node is not None
            and self.last_pressed_node == self.last_picked_node
            and self.move_objects
        ):
            position = np.array([event.ydata, event.xdata])
            self.action_history.add(
                actions.NodeMove(
                    self.last_pressed_node,
                    self.ax,
                    self.origin,
                    position,
                    self.node_plot,
                    self.pick_node,
                    self.edge_sets_for_nodes,
                )
            )
        if (
            self.last_pressed_way_point is not None
            and self.last_pressed_way_point == self.last_picked_way_point
            and self.move_objects
        ):
            edge, index = self.last_pressed_way_point
            position = np.array([event.ydata, event.xdata])
            self.action_history.add(
                actions.EdgeWaypointMove(
                    edge,
                    self.ax,
                    index,
                    self.origin,
                    position,
                    self.pick_edge,
                    self.pick_waypoint,
                )
            )
            print_grey("moved point")
        self.last_pressed_way_point = None
        self.last_pressed_node = None

    def delete(self) -> None:
        """
        called when user wants to delete an object

        :return: None
        """
        if self.last_picked_edge is not None:
            if self.last_picked_way_point is not None:
                print_grey("deleting waypoint")
                edge_plot, point_index = self.last_picked_way_point
                self.action_history.add(
                    actions.EdgeWaypointDeletion(
                        edge_plot, point_index, self.ax, self.origin, self.pick_edge
                    )
                )
                self.last_picked_way_point = None
            else:
                print_grey("deleting edge")
                self.action_history.add(
                    actions.EdgeDeletion(
                        self.last_picked_edge,
                        self.ax,
                        self.graph,
                        self.pick_edge,
                        self.edge_sets_for_nodes,
                    )
                )
                self.last_picked_edge = None
        elif self.last_picked_node is not None:
            if len(self.node_plot.node_list[self.last_picked_node].edges) > 0:
                print_grey("node has edges assigned to it and cannot be deleted")
            else:
                print_grey("deleting Node")
                self.action_history.add(
                    actions.NodeDeletion(
                        self.last_picked_node,
                        self.graph,
                        self.ax,
                        self.origin,
                        self.node_plot,
                        self.set_nodes,
                        self.pick_node,
                    )
                )
                self.last_picked_node = None
        else:
            print_grey("no object to delete")

    def undo(self) -> None:
        """
        called for undo action

        :return: None
        """
        print_grey("undo")
        self.action_history.undo()

    def redo(self) -> None:
        """
        called for redo action

        :return: None
        """
        print_grey("redo")
        self.action_history.redo()

    def move(self) -> None:
        """
        called when user switches state of movement

        :return: None
        """
        print_grey("toggling movement to {}".format(not self.move_objects))
        self.move_objects = not self.move_objects
        # propagate movement to embedding
        self.update_movement(self.move_objects)

    def split(self) -> None:
        """
        called when a user splits an edge into two at a way point

        :return: None
        """
        if self.last_picked_way_point is not None:
            self.action_history.add(
                actions.EdgeSplit(
                    self.last_picked_way_point[1],
                    self.last_picked_edge,
                    self.origin,
                    self.ax,
                    self.node_plot,
                    self.graph,
                    self.edges,
                    self.edge_sets_for_nodes,
                    self.set_nodes,
                    self.pick_node,
                    self.pick_edge,
                )
            )
        else:
            print_grey("select a waypoint to split the edge at")

    def new_waypoint(self) -> None:
        """
        called to create a new way point

        :return: None
        """
        if self.last_picked_edge is not None:
            print_grey("creating new waypoint")
            if self.last_picked_way_point is not None:
                pos = self.last_picked_way_point[1]
            else:
                pos = 0
            self.action_history.add(
                actions.EdgeWaypointAddition(
                    self.last_picked_edge,
                    pos,
                    self.pick_edge,
                    self.pick_waypoint,
                    self.ax,
                    self.origin,
                )
            )
        else:
            print_grey("waypoint cannot be created: no edge selected")

    def save(self) -> None:
        """
        save current state of the edit to disk

        :return None
        """
        name = "edge_save_{}.save".format(
            datetime.datetime.now().strftime("%y-%m-%d_%H-%M-%S")
        )
        check_dir("files/edge_edit_saves")
        Tk().withdraw()
        file = asksaveasfilename(
            initialdir="files/edge_edit_saves",
            initialfile=name,
            defaultextension=".save",
            filetypes=(("save file", "*.save"), ("All Files", "*.*")),
        )
        if file != "" and file is not None:
            self.save_state(file)

    def load(self) -> None:
        """
        load an old state of the edit to disk

        :return: None
        """
        Tk().withdraw()
        check_dir("files/edge_edit_saves")
        self.load_state(
            askopenfilename(
                initialdir="files/edge_edit_saves",
                filetypes=(("save files", "*.save"), ("all files", "*.*")),
            )
        )

    def load_state(self, filename: str) -> None:
        """
        loads an edit state from disk

        :return: None
        """
        super().load_state(filename)

    def create_edge(self) -> None:
        """
        called when user wants to create a new edge, starts edge create mode

        :return: None
        """
        if self.last_picked_node is not None:
            print_grey("creating edge")
            self.edge_create_mode = True
            assert self.last_picked_edge is None
            assert self.last_picked_way_point is None
            self.new_edge_start_node = self.node_plot.node_list[self.last_picked_node]
            self.new_edge_waypoint_plots = []
            self.new_edge_waypoints = []
        else:
            print_grey("pick a node to create an edge")

    def edit_width(self) -> None:
        """
        allows to edit the width of lanes, then applies the new widths to the graph

        :return: None
        """
        self.old_lane_widths = copy.deepcopy(config.LANEWIDTHS)
        self.width_edit_window = EditLaneWidths(self.update_widths)

    def update_widths(self) -> None:
        """
        sets the widths of all lanes to the value saved in config.py

        :return: None
        """
        self.action_history.add(
            actions.LaneWidthEditing(
                self.graph, self.unhighlight, self.ax, self.old_lane_widths
            )
        )


class EditLaneWidths(EditLaneWidth):
    """
    allows to edit the width of lanes
    this inherits from the settings window
    """

    def __init__(self, update_fun: Callable[[], None]):
        """

        :param update_fun: a function which is called to update the edge widths
        """
        self.update_widths: Callable[[], None] = update_fun
        super().__init__()

    def accept(self) -> None:
        """
        saves the values and updates with update function

        :return: None
        """
        self.save()
        self.update_widths()
        self.original_accept()


def print_grey(text) -> None:
    """
    allows to print outputs in grey color, which makes it distinguishable which outputs belong to gui actions

    :param text:
    :return: None
    """
    print("\033[90m" + str(text) + "\033[0m")


def edit_graph_edges(graph: rg.Graph) -> rg.Graph:
    """
    starts a GUI to edit the edges of a graph

    :param graph: the graph to edit
    :return: the edited graph
    """
    ee_gui = EdgeEditGUI(graph, None, None, None)
    while ee_gui.restart:
        ee_gui = ee_gui.new_gui
        assert ee_gui is not None
        assert type(ee_gui) == EdgeEditGUI
        ee_gui.setup_event_listeners(ee_gui.fig.canvas)
        ee_gui.restart = False
    return ee_gui.graph


def edit_graph_links(graph: rg.Graph) -> rg.Graph:
    """
    starts a GUI to edit the lane links of a graph

    :param graph: the graph to edit
    :return: the edited graph
    """
    ll_gui = LaneLinkGUI(graph, None)
    while ll_gui.restart:
        ll_gui = ll_gui.new_gui
        assert ll_gui is not None
        assert type(ll_gui) == LaneLinkGUI
        ll_gui.setup_event_listeners(ll_gui.fig.canvas)
        ll_gui.restart = False
    return ll_gui.graph
