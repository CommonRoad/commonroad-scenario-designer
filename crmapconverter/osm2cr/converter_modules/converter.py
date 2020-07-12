"""
This module provides the main functionality to perform a conversion.
You can use this module instead of using **main.py**.
"""
import pickle
import sys

import matplotlib.pyplot as plt

from crmapconverter.osm2cr import config
from crmapconverter.osm2cr.converter_modules.cr_operations import export
from crmapconverter.osm2cr.converter_modules.graph_operations import (
    lane_linker,
    segment_clusters,
    offsetter,
    road_graph,
    intersection_merger,
)
from crmapconverter.osm2cr.converter_modules.gui_modules import gui
from crmapconverter.osm2cr.converter_modules.osm_operations import osm_parser
from crmapconverter.osm2cr.converter_modules.utility import plots


def step_collection_1(g: road_graph.Graph) -> road_graph.Graph:
    if config.MAKE_CONTIGUOUS:
        print("making graph contiguously")
        g.make_contiguous()
    print("merging close intersections")
    intersection_merger.merge_close_intersections(g)
    g.link_edges()
    if isinstance(g.sublayer_graph, road_graph.SublayeredGraph):
        g.sublayer_graph = step_collection_1(g.sublayer_graph)
    return g


def step_collection_2(g: road_graph.Graph) -> road_graph.Graph:
    print("linking lanes")
    lane_linker.link_graph(g)
    print("interpolating waypoints")
    g.interpolate()
    print("offsetting roads")
    offsetter.offset_graph(g)
    print("cropping roads at intersections")
    g.crop_waypoints_at_intersections()
    if config.DELETE_SHORT_EDGES:
        print("deleting short edges")
    print("applying traffic signs to edges and nodes")
    g.apply_traffic_signs()
    print("applying traffic lights to edges")
    g.apply_traffic_lights()
    print("creating waypoints of lanes")
    g.create_lane_waypoints()
    if isinstance(g.sublayer_graph, road_graph.SublayeredGraph):
        temp_intersec_dist = config.INTERSECTION_DISTANCE
        config.INTERSECTION_DISTANCE = config.INTERSECTION_DISTANCE_PEDESTRIAN
        g.sublayer_graph = step_collection_2(g.sublayer_graph)
        config.INTERSECTION_DISTANCE = temp_intersec_dist
    return g


def step_collection_3(g: road_graph.Graph) -> road_graph.Graph:
    print("creating segments at intersections")
    g.create_lane_link_segments()
    print("clustering segments")
    segment_clusters.cluster_segments(g)
    print(
        "changing to desired interpolation distance and creating borders of lanes"
    )
    g.create_lane_bounds(
        config.INTERPOLATION_DISTANCE_INTERNAL / config.INTERPOLATION_DISTANCE
    )
    print("adjust common bound points")
    g.correct_start_end_points()
    print("done converting")
    if isinstance(g.sublayer_graph, road_graph.SublayeredGraph):
        g.sublayer_graph = step_collection_3(g.sublayer_graph)
    return g


class GraphScenario:
    """
    Class that represents a road network
    data is saved by a graph structure (RoadGraph)

    """

    def __init__(self, file: str):
        """
        loads an OSM file and converts it to a graph

        :param file: OSM file to be loaded
        :type file: str
        """
        print("reading File and creating graph")
        g = osm_parser.create_graph(file)
        g = step_collection_1(g)
        # HERE WE CAN EDIT THE NODES AND EDGES OF THE GRAPH
        if config.USER_EDIT:
            print("editing the graph")
            g = gui.edit_graph_edges(g)
        g = step_collection_2(g)
        # HERE WE CAN EDIT LINKS IN THE GRAPH
        if config.USER_EDIT:
            print("editing the graph")
            g = gui.edit_graph_links(g)
        g = step_collection_3(g)
        self.graph: road_graph.Graph = g

    def plot(self):
        """
        plots the graph and shows it

        :return: None
        """
        print("plotting graph")
        _, ax = plt.subplots()
        ax.set_aspect("equal")
        plots.draw_scenario(self.graph, ax)
        plots.show_plot()

    def save_as_cr(self, filename: str):
        """
        exports the road network to a CommonRoad scenario

        :param filename: file name for scenario generation tool
        :return: None
        """
        if filename is not None:
            export.export(self.graph, filename)
        else:
            export.export(self.graph)

    def save_to_file(self, filename: str):
        """
        Saves the road network to a file and stores it on disk

        :param filename: name of the file to save
        :type filename: str
        :return: None
        """
        sys.setrecursionlimit(10000)
        with open(filename, "wb") as handle:
            pickle.dump(self, handle, protocol=pickle.HIGHEST_PROTOCOL)
        sys.setrecursionlimit(1000)


def load_from_file(filename: str) -> GraphScenario:
    """
    loads a road network from a file
    Warning! Do only load files you trust!

    :param filename: name of the file to load
    :type filename: str
    :return: the loaded road network
    :rtype: Scenario
    """
    with open(filename, "rb") as handle:
        scenario = pickle.load(handle)
        return scenario