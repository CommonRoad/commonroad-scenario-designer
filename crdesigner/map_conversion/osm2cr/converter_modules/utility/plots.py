"""
This module provides many functions to plot a scenario.
It is not used in the conversion process.
"""
import matplotlib.pyplot as plt
import matplotlib.axes as axis
import numpy as np
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations import road_graph as rg


def draw_laneborders(lane: rg.Lane, ax: axis):
    """
    draws a single lane in a plot

    :param ax: the ax object to draw on
    :param lane: lane object
    :type lane: Lane
    :return: None
    """
    x_points = []
    y_points = []
    if len(lane.left_bound) > 0 and len(lane.right_bound) > 0:
        for x_current, y_current in lane.left_bound:
            x_points.append(x_current)
            y_points.append(y_current)
        for x_current, y_current in reversed(lane.right_bound):
            x_points.append(x_current)
            y_points.append(y_current)
        x_points.append(lane.left_bound[0][0])
        y_points.append(lane.left_bound[0][1])
        ax.plot(x_points, y_points, color="black", linewidth=1.0)
        # plotter.scatter(x_points, y_points, color='grey', s=4)
    return


def draw_edge_orientation(edge: rg.GraphEdge, ax: axis):
    """
    draws a single edge direction in a plot

    :param ax: the ax object to draw on
    :param edge: edge object

    :return: None
    """

    # draw an arrow from start to end of edge
    ax.scatter(edge.node1.x, edge.node1.y, color="blue")
    ax.arrow(x=edge.node1.x,  y=edge.node1.y,  dx=edge.node2.x - edge.node1.x,  dy=edge.node2.y - edge.node1.y,
             color="red",  width=1, head_width=6)
    # print compass degrees
    ax.text(
        x=(edge.node1.x + edge.node2.x)/2,
        y=(edge.node1.y + edge.node2.y)/2,
        s='{}'.format(int(edge.get_compass_degrees()))
        )


def draw_lanelet_direction(lane: rg.Lane, ax: axis):
    """
    draws a single lane direction in a plot. Green if lane forward

    :param ax: the ax object to draw on
    :param lane: lane object

    :return: None
    """
    ax.arrow(
        x=lane.right_bound[0][0],
        y=lane.right_bound[0][1],
        dx=lane.right_bound[-1][0] - lane.right_bound[0][0],
        dy=lane.right_bound[-1][1] - lane.right_bound[0][1],
        color="green" if lane.forward else "pink",
        width=1,
        head_width=2)


def draw_graph(graph: rg.Graph, ax: axis, links: bool = True):
    """
    draws lanelets of a graph in a plot

    :param ax: the ax object to draw on
    :param graph: road graph
    :type graph: Graph
    :return: None
    """

    # USE THIS FOR DEBUGGING
    debug = False

    counter = 0
    lanes = []
    for edge in graph.edges:
        lanes += edge.lanes
        if debug:
            draw_edge_orientation(edge, ax)

    if links:
        lanes += list(graph.lanelinks)
    for lane in lanes:
        if counter % 100 == 0:
            print("drawing lanelet {} of {}".format(counter, len(lanes)))
        draw_laneborders(lane, ax)
        if debug:
            draw_lanelet_direction(lane, ax)
        counter += 1

    return


def draw_nodes(graph: rg.Graph, ax: axis):
    """
    scatters the nodes of a graph on the plot

    :param ax: the ax object to draw on
    :param graph: graph
    :type graph: Graph
    :return: None
    """
    nodes_x, nodes_y = [], []
    for node in graph.nodes:
        nodes_x.append(node.x)
        nodes_y.append(node.y)
    ax.scatter(nodes_x, nodes_y)
    return


def draw_simple_edges(graph: rg.Graph, ax: axis):
    """
    draws the edges of a graph simplified by a straight line between its start and end

    :param ax: the ax object to draw on
    :param graph: graph
    :type graph: Graph
    :return: None
    """
    for edge in graph.edges:
        ax.plot([edge.node1.x, edge.node2.x], [edge.node1.y, edge.node2.y])
    return


def draw_edges(graph: rg.Graph, ax: axis):
    """
    draws the edges of a graph according to their original way points

    :param ax: the ax object to draw on
    :param graph: graph
    :type graph: Graph
    :return: None
    """
    for edge in graph.edges:
        waypoints_x, waypoints_y = [], []
        for waypoint in edge.waypoints:
            waypoints_x.append(waypoint.x)
            waypoints_y.append(waypoint.y)
        ax.plot(waypoints_x, waypoints_y, color="black")
    return


def draw_interpolated_edges(graph: rg.Graph, ax: axis):
    """
    draws the interpolated courses of the edges of a graph

    :param ax: the ax object to draw on
    :param graph: graph
    :type graph: Graph
    :return: None
    """
    for edge in graph.edges:
        waypoints_x, waypoints_y = [], []
        for waypoint in edge.interpolated_waypoints:
            waypoints_x.append(waypoint[0])
            waypoints_y.append(waypoint[1])
        ax.plot(waypoints_x, waypoints_y, color="black")
    return


def draw_lane(lane: rg.Lane, ax: axis):
    """
    draws a lane

    :param ax: the ax object to draw on
    :param lane: lane
    :type lane: Lane
    :return: None
    """
    waypoints_x, waypoints_y = [], []
    for waypoint in lane.waypoints:
        waypoints_x.append(waypoint[0])
        waypoints_y.append(waypoint[1])
    ax.plot(waypoints_x, waypoints_y, color="black")
    return


def draw_lanes(graph: rg.Graph, ax: axis, links: bool = True):
    """
    draws all lanes of a graph

    :param ax: the ax object to draw on
    :param graph: graph
    :type graph: Graph
    :return: None
    """
    for edge in graph.edges:
        for lane in edge.lanes:
            draw_lane(lane, ax)
    if links:
        for lane in graph.lanelinks:
            draw_lane(lane, ax)
    return


def draw_edge_links(graph: rg.Graph, ax: axis):
    """
    draws all links between edges of a graph with arrows

    :param ax: the ax object to draw on
    :param graph: graph
    :type graph: Graph
    :return: None
    """
    for edge in graph.edges:
        if edge.forward_successor is not None:
            from_point = edge.interpolated_waypoints[-1]
            to_point = edge.forward_successor.interpolated_waypoints[0]
            dx = to_point[0] - from_point[0]
            dy = to_point[1] - from_point[1]
            length = np.sqrt(dx ** 2 + dy ** 2)
            ax.arrow(
                from_point[0],
                from_point[1],
                dx,
                dy,
                head_width=0.5,
                head_length=1,
                length_includes_head=(0.1 < length),
            )
        if edge.backward_successor is not None:
            from_point = edge.interpolated_waypoints[0]
            to_point = edge.backward_successor.interpolated_waypoints[-1]
            dx = to_point[0] - from_point[0]
            dy = to_point[1] - from_point[1]
            length = np.sqrt(dx ** 2 + dy ** 2)
            ax.arrow(
                from_point[0],
                from_point[1],
                dx,
                dy,
                head_width=0.5,
                head_length=1,
                length_includes_head=(0.1 < length),
            )
    return


def draw_lane_links(graph: rg.Graph, ax: axis):
    """
    draws all links between lanes of a graph with arrows

    :param ax: the ax object to draw on
    :param graph: graph
    :type graph: Graph
    :return: None
    """
    for edge in graph.edges:
        for lane in edge.lanes:
            last_point = lane.waypoints[-1]
            for successor in lane.successors:
                first_point = successor.waypoints[0]
                dx = first_point[0] - last_point[0]
                dy = first_point[1] - last_point[1]
                length = np.sqrt(dx ** 2 + dy ** 2)
                ax.arrow(
                    last_point[0],
                    last_point[1],
                    dx,
                    dy,
                    head_width=1,
                    head_length=2,
                    length_includes_head=(0.1 < length),
                )
    return


def draw_points_of_lane(lane: rg.Lane, ax: axis):
    waypoints_x, waypoints_y = [], []
    for waypoint in lane.waypoints + lane.left_bound + lane.right_bound:
        waypoints_x.append(waypoint[0])
        waypoints_y.append(waypoint[1])
    ax.scatter(waypoints_x, waypoints_y)


def draw_all_points(graph: rg.Graph, ax: axis):
    """
    draws all points of all lanelets in the scenario

    :param graph:
    :param ax:
    :return:
    """
    for lane in graph.get_all_lanes():
        draw_points_of_lane(lane, ax)


def show_plot():
    """
    shows the plot

    :return: None
    """
    plt.show()
    return


def save_fig(filename: str, x1: float, x2: float, y1: float, y2: float, ax: axis):
    """
    saves a specified area of the plot to a file

    :param filename: name of the file
    :type filename: str
    :param x1: left bound of the figure
    :type x1: float
    :param x2: right bound of the figure
    :type x2: float
    :param y1: lower bound of the figure
    :type y1: float
    :param y2: upper bound of the figure
    :type y2: float
    :param ax: the ax object to draw on
    :return: None
    """
    plt.axis("off")
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.set_xlim(x1, x2)
    ax.set_ylim(y1, y2)
    plt.savefig(filename, bbox_inches="tight", pad_inches=0)
    return
