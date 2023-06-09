"""
This module holds all interaction between this application and the ***CommonRoad python tools**.
It allows to export a scenario to CR or plot a CR scenario.
"""
from typing import List, Tuple

import logging
import numpy as np
import utm

from crdesigner.map_conversion.osm2cr import config
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations import road_graph as rg
from crdesigner.map_conversion.osm2cr.converter_modules.intermediate_operations.intermediate_format import \
    IntermediateFormat
from crdesigner.map_conversion.common import geometry
from crdesigner.map_conversion.osm2cr.converter_modules.utility.idgenerator import get_id
from crdesigner.map_conversion.osm2cr.converter_modules.utility.geonamesID import get_geonamesID
from crdesigner.map_conversion.osm2cr.converter_modules.cr_operations.cleanup import sanitize

# CommonRoad python tools are imported
from commonroad.visualization.mp_renderer import MPRenderer
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.scenario.scenario import Scenario, Lanelet, Tag, Location


def get_lanelet(lane: rg.Lane) -> Lanelet:
    """
    converts a graph lane to a lanelet

    :param lane: the graph lane to be converted
    :return: the resulting lanelet
    """
    current_id = lane.id
    left_bound = lane.left_bound
    right_bound = lane.right_bound
    center_points = lane.waypoints
    successors = []
    # speedlimit = lane.speedlimit
    # if speedlimit is None or speedlimit == 0:
    #     speedlimit = np.infty
    for successor in lane.successors:
        successors.append(successor.id)
    predecessors = []
    for predecessor in lane.predecessors:
        predecessors.append(predecessor.id)
    # left adjacent
    if lane.adjacent_left is not None:
        adjacent_left = lane.adjacent_left.id
        if lane.adjacent_left_direction_equal is not None:
            adjacent_left_direction_equal = lane.adjacent_left_direction_equal
        elif lane.edge is not None:
            adjacent_left_direction_equal = lane.forward == adjacent_left.forward
        else:
            raise ValueError("Lane has no direction info!")
    else:
        adjacent_left = None
        adjacent_left_direction_equal = None
    # right adjacent
    if lane.adjacent_right is not None:
        adjacent_right = lane.adjacent_right.id
        if lane.adjacent_right_direction_equal is not None:
            adjacent_right_direction_equal = lane.adjacent_right_direction_equal
        elif lane.edge is not None:
            adjacent_right_direction_equal = lane.forward == adjacent_right.forward
        else:
            raise ValueError("Lane has no direction info!")
    else:
        adjacent_right = None
        adjacent_right_direction_equal = None
    # print("len of polylines: {}/{}/{}".format(len(left_bound), len(center_points), len(right_bound)))
    lanelet = Lanelet(
        np.array(left_bound),
        np.array(center_points),
        np.array(right_bound),
        current_id,
        predecessors,
        successors,
        adjacent_left,
        adjacent_left_direction_equal,
        adjacent_right,
        adjacent_right_direction_equal,
    )
    return lanelet


def get_lanelets(graph: rg.Graph) -> List[Lanelet]:
    """
    converts each lane in a graph to a lanelet and returns a list of all lanelets

    :param graph: the graph to convert
    :return: list of lanelets
    """
    result = []
    for lane in graph.get_all_lanes():
        lane.id = get_id()
    for edge in graph.edges:
        for lane in edge.lanes:
            result.append(get_lanelet(lane))
    for lane in graph.lanelinks:
        result.append(get_lanelet(lane))
    return result


# def create_scenario(graph: rg.Graph) -> Scenario:
#     """
#     creates a CR scenario out of a graph

#     :param graph: the graph to convert
#     :return: CR scenario
#     """
#     scenario = Scenario(config.TIMESTEPSIZE, config.BENCHMARK_ID)
#     net = LaneletNetwork()
#     for lanelet in get_lanelets(graph):
#         net.add_lanelet(lanelet)
#     scenario.lanelet_network = net
#     return scenario


def convert_coordinates_to_utm(scenario: Scenario, origin: np.ndarray) -> None:
    """
    converts all cartesian in scenario coordinates to utm coordinates

    :param scenario: the scenario to convert
    :param origin: origin of the cartesian coordinate system in lat and lon
    :return: None
    """
    for lanelet in scenario.lanelet_network.lanelets:
        for bound in [
            lanelet._left_vertices,
            lanelet._right_vertices,
            lanelet._center_vertices,
        ]:
            for index, point in enumerate(bound):
                point = geometry.cartesian_to_lon_lat(point, origin)
                lon = point[0]
                lat = point[1]
                easting, northing, zone_number, zone_letter = utm.from_latlon(lat, lon)
                bound[index] = np.array([easting, northing])
    return


def create_scenario_intermediate(graph) -> Tuple[Scenario, IntermediateFormat]:
    """ Convert Scenario from RoadGraph via IntermediateFormat """
    interm = IntermediateFormat.extract_from_road_graph(graph)
    if isinstance(graph, rg.SublayeredGraph):
        interm_sublayer = IntermediateFormat.extract_from_road_graph(
            graph.sublayer_graph)
        crossings = IntermediateFormat.get_lanelet_intersections(interm_sublayer, interm)
        interm_sublayer.intersections = list()
        interm_sublayer.traffic_signs = list()
        interm_sublayer.traffic_lights = list()
        interm_sublayer.remove_invalid_references()
        print("removed intersections, traffic lights, traffic signs from sublayer")
        interm.merge(interm_sublayer)
        interm.add_crossing_information(crossings)
    scenario = interm.to_commonroad_scenario()
    return scenario, interm


def export(
        graph: rg.Graph,
        file_path=config.SAVE_PATH + config.BENCHMARK_ID + ".xml"
) -> None:
    """
    converts a graph to a CR scenario and saves it to disk

    :param graph: the graph
    :return: None
    """
    # scenario = create_scenario(graph)
    scenario, intermediate_format = create_scenario_intermediate(graph)
    # removing converting errors before writing to xml
    sanitize(scenario)

    # writing everything to XML
    logging.info("writing scenario to XML file")

    if config.EXPORT_IN_UTM:
        convert_coordinates_to_utm(scenario, graph.center_point)
    problemset = intermediate_format.get_dummy_planning_problem_set()
    author = config.AUTHOR
    affiliation = config.AFFILIATION
    source = config.SOURCE
    if config.MAPILLARY_CLIENT_ID != "demo":
        source += ", Mapillary"
    tags = create_tags(config.TAGS)
    # create location tag automatically. Retreive geonamesID from the Internet.
    location = Location(gps_latitude=graph.center_point[0],
                        gps_longitude=graph.center_point[1],
                        geo_name_id=get_geonamesID(graph.center_point[0], graph.center_point[1]),
                        geo_transformation=None)
    # in the current commonroad version the following line works
    file_writer = CommonRoadFileWriter(
        scenario, problemset, author, affiliation, source, tags, location, decimal_precision=16)

    # write scenario to file with planning problem
    file_writer.write_to_file(file_path, OverwriteExistingFile.ALWAYS)

    # write scenario to file without planning problem
    # file_writer.write_scenario_to_file(file, OverwriteExistingFile.ALWAYS)


def convert_to_scenario(graph: rg.Graph) -> Scenario:
    # scenario = create_scenario(graph)
    scenario, intermediate_format = create_scenario_intermediate(graph)
    # removing converting errors before writing to xml
    sanitize(scenario)
    return scenario


def create_tags(tags: str):
    """
    creates tags out of a space separated string

    :param tags: string of tags
    :return: list of tags
    """
    splits = tags.split()
    tags = set()
    for tag in splits:
        tags.add(Tag(tag))
    return tags


def find_bounds(scenario: Scenario) -> List[float]:
    """
    finds the bounds of the scenario

    :param scenario: the scenario of which the bounds are found
    :return: list of bounds
    """
    x_min = min(
        [
            min(point[0] for point in lanelet.center_vertices)
            for lanelet in scenario.lanelet_network.lanelets
        ]
    )
    x_max = max(
        [
            max(point[0] for point in lanelet.center_vertices)
            for lanelet in scenario.lanelet_network.lanelets
        ]
    )
    y_min = min(
        [
            min(point[1] for point in lanelet.center_vertices)
            for lanelet in scenario.lanelet_network.lanelets
        ]
    )
    y_max = max(
        [
            max(point[1] for point in lanelet.center_vertices)
            for lanelet in scenario.lanelet_network.lanelets
        ]
    )
    return [x_min, x_max, y_min, y_max]


def view_xml(filename: str, ax=None) -> None:
    """
    shows the plot of a CR scenario on a axes object
    if no axes are provided, a new window is opened with pyplot

    :param filename: file of scenario
    :param ax: axes to plot on
    :return: None
    """
    print("loading scenario from XML")
    scenario, problem = CommonRoadFileReader(filename).open()
    print("drawing scenario")
    if len(scenario.lanelet_network.lanelets) == 0:
        print("empty scenario")
        return
    limits = find_bounds(scenario)

    draw_params = {'lanelet_network': {'draw_intersections': True, 'draw_traffic_signs_in_lanelet': True,
                                       'draw_traffic_signs': True, 'draw_traffic_lights': True,
                                       'intersection': {'draw_intersections': True},
                                       'traffic_sign': {'draw_traffic_signs': True,
                                                        'show_label': False,
                                                        'show_traffic_signs': 'all',

                                                        'scale_factor': 0.15}},
                   'lanelet': {'show_label': False}}
    rnd = MPRenderer(plot_limits=limits, ax=ax, draw_params=draw_params)
    scenario.draw(rnd)
    rnd.render()
