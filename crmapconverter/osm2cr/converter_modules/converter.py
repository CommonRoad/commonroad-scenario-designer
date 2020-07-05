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
            traffic_lights, crossing_points) = osm_parser.parse_file(
            file, accepted_highways, config.REJECTED_TAGS, custom_bounds
        )
        print("creating graph")
        graph = osm_parser.roads_to_graph(
            roads, points, restrictions, center_point, bounds, center_point,
            traffic_signs, traffic_lights, additional_nodes
        )
        return graph, crossing_points

    if config.EXTRACT_PATHWAYS:
        all_accepted_ways = config.ACCEPTED_HIGHWAYS.copy()
        all_accepted_ways.extend(config.ACCEPTED_PATHWAYS)
        combined_g, _ = create_graph(osm_file, all_accepted_ways)
        road_g, road_crossing_points = create_graph(osm_file,
            config.ACCEPTED_HIGHWAYS, combined_g.bounds)
        path_g, path_crossing_points = create_graph(osm_file,
            config.ACCEPTED_PATHWAYS, combined_g.bounds)

        crossing_nodes = set()
        already_contained = set()
        road_nodes = {node.id: node for node in road_g.nodes}
        for p_id, point in road_crossing_points.items():
            if p_id in path_crossing_points and not is_close_to_intersection2(
                p_id, combined_g, road_g
            ):
                if p_id in road_nodes:
                    already_contained.add(p_id)
                else:
                    crossing_node = road_graph.GraphNode(
                        int(p_id), point.x, point.y, set()
                    )
                    crossing_node.is_crossing = True
                    crossing_nodes.add(crossing_node)

        graph, _ = create_graph(osm_file, config.ACCEPTED_HIGHWAYS,
            combined_g.bounds, crossing_nodes)
        for node in graph.nodes:
            if node.id in already_contained:
                node.is_crossing = True
        graph.sublayer = path_g
    else:
        graph = create_graph(osm_file, config.ACCEPTED_HIGHWAYS)
    return graph


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
        temp_intersec_dist = config.INTERSECTION_DISTANCE
        config.INTERSECTION_DISTANCE = 1.0
        g.sublayer = step_collection_2(g.sublayer)
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
    if not g.sublayer is None:
        g.sublayer = step_collection_3(g.sublayer)
    return g


def is_close_to_intersection2(node_id, combined_graph, road_g):
    node = [nd for nd in combined_graph.nodes if nd.id == node_id][0]
    road_node_ids = [nd.id for nd in road_g.nodes]

    for edge in node.edges:
        if node == edge.node1:
            neighbor = edge.node2
        else:
            neighbor = edge.node1
        if (neighbor.id in road_node_ids and neighbor.get_degree() > 2
                and neighbor.get_distance(node) < config.INTERSECTION_DISTANCE/2.0
        ):
            # close neighbor is intersection
            print(node, "is too close to intersection at", neighbor)
            return True
    return False


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
