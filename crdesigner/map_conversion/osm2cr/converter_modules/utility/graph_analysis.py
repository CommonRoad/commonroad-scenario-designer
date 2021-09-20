"""
This module provides functions to analyse the available data.
It is not used in the conversion process.
"""
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations import road_graph


def count_given_lanes(graph: road_graph.Graph):
    """
    counts and prints frequency of lane and turnlane information

    :param graph: graph object
    :type graph: Graph
    :return: None
    """
    given_nr_of_lanes, given_nr_and_directions_of_lanes = 0, 0
    for edge in graph.edges:
        if edge.nr_of_lanes is not None:
            given_nr_of_lanes += 1
        if edge.forward_lanes is not None:
            given_nr_and_directions_of_lanes += 1
    print(
        "Nr of {} lanes given, direction of {} lanes given, total: {} lanes"
        "".format(given_nr_of_lanes, given_nr_and_directions_of_lanes, len(graph.edges))
    )
    return


def count_degrees(graph: road_graph.Graph):
    """
    counts and prints the frequency of the degrees of nodes in a graph

    :param graph: graph object
    :type graph: Graph
    :return: None
    """
    degrees = {}
    for node in graph.nodes:
        if node.get_degree() in degrees:
            degrees[node.get_degree()] += 1
        else:
            degrees[node.get_degree()] = 1
    print(degrees)
    return
