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


def osm_to_graph(osm_file) -> road_graph.Graph:
    def create_graph(
            file, accepted_highways, custom_bounds=None, additional_nodes=None):
        print("reading File")
        (roads, points, restrictions, center_point, bounds, traffic_signs,
            traffic_lights) = osm_parser.parse_file(
            file, accepted_highways, config.REJECTED_TAGS, custom_bounds
        )
        print("creating graph")
        graph = osm_parser.roads_to_graph(
            roads, points, restrictions, center_point, bounds, center_point,
            traffic_signs, traffic_lights, additional_nodes
        )
        return graph

    if config.EXTRACT_PATHWAYS:
        all_accepted_ways = config.ACCEPTED_HIGHWAYS.copy()
        all_accepted_ways.extend(config.ACCEPTED_PATHWAYS)
        combined_g = create_graph(osm_file, all_accepted_ways)
        highway_g = create_graph(osm_file, config.ACCEPTED_HIGHWAYS,
            combined_g.bounds)
        pathway_g = create_graph(osm_file, config.ACCEPTED_PATHWAYS,
            combined_g.bounds)
        crossing_nodes = node_difference(combined_g.nodes, highway_g.nodes, pathway_g.nodes)
        for n in crossing_nodes:
            n.edges.clear()
            n.is_crossing = True
        g = create_graph(osm_file, config.ACCEPTED_HIGHWAYS, combined_g.bounds,
            crossing_nodes)
        g.sublayer = pathway_g
    else:
        g = create_graph(osm_file, config.ACCEPTED_HIGHWAYS)
    return g


def step_collection_1(g: road_graph.Graph) -> road_graph.Graph:
    if config.MAKE_CONTIGUOUS:
        print("making graph contiguously")
        g.make_contiguous()
    print("merging close intersections")
    intersection_merger.merge_close_intersections(g)
    g.link_edges()
    if not g.sublayer is None:
        g.sublayer = step_collection_1(g.sublayer)
    return g

def step_collection_2(g: road_graph.Graph) -> road_graph.Graph:
    print("linking lanes")
    lane_linker.link_graph(g)
    print("interpolating waypoints")
    g.interpolate()
    print("offsetting roads")
    offsetter.offset_graph(g)
    print("cropping roads at intersections")
    edges_to_delete = g.crop_waypoints_at_intersections()
    if config.DELETE_SHORT_EDGES:
        print("deleting short edges")
        g.delete_edges(edges_to_delete)
    print("applying traffic signs to edges and nodes")
    g.apply_traffic_signs()
    print("applying traffic lights to edges")
    g.apply_traffic_lights()
    print("creating waypoints of lanes")
    g.create_lane_waypoints()
    if not g.sublayer is None:
        g.sublayer = step_collection_2(g.sublayer)
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
    if not g.sublayer is None:
        g.sublayer = step_collection_3(g.sublayer)
    return g


def is_close_to_intersection(node):
    for edge in node.edges:
        if node == edge.node1:
            neighbor = edge.node2
        else:
            neighbor = edge.node1
        if neighbor.get_distance(node) < config.INTERSECTION_DISTANCE and neighbor.get_degree() > 2:
            # close neighbor is intersection
            print(node, "is too close to intersection at", neighbor)
            return True
    return False


def node_difference(nodes0, nodes1, nodes2):
    """
    Returns all nodes that are only part of the combined nodes.
    """
    # get crossing points
    result_nodes = []
    for candidate_node in nodes0:
        is_contained = False
        for node in nodes1:
            is_contained |= node.id == candidate_node.id
        for node in nodes2:
            is_contained |= node.id == candidate_node.id
        if not is_contained and not is_close_to_intersection(candidate_node):
            # remove all information about edges from earlier linking
            result_nodes.append(candidate_node)
    return result_nodes


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
        g = osm_to_graph(file)
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
