from matplotlib import pyplot as plt

from commonroad.visualization.draw_dispatch_cr import draw_object
from commonroad.common import file_writer
from crmapconverter.osm2cr import config
from crmapconverter.osm2cr.converter_modules.converter import Scenario
from crmapconverter.osm2cr.converter_modules.intermediate_format.intermediate_format import IntermediateFormat
# from crmapconverter.osm2cr.converter_modules.utility.geometry import lon_lat_to_cartesian
from crmapconverter.osm2cr.converter_modules.osm_operations import osm_parser
from crmapconverter.osm2cr.converter_modules.graph_operations import intersection_merger
from crmapconverter.osm2cr.converter_modules.cr_operations import export
from crmapconverter.osm2cr.converter_modules.cr_operations import cleanup

scenario_file = "/home/max/Desktop/Planning/Maps/osm_files/garching_kreuzung_fixed.osm"
# scenario_file = "/home/max/Desktop/Planning/Maps/osm_files/only_straigt_test.osm"
# scenario_file = "/home/max/Desktop/Planning/Maps/osm_files/intersect_and_crossing2.osm"
target_file = "/home/max/Desktop/Planning/Maps/cr_files/garching_kreuzung_merged.xml"
# target_file = "/home/max/Desktop/Planning/Maps/cr_files/only_straigt_merged.xml"
# target_file = "/home/max/Desktop/Planning/Maps/cr_files/intersect_and_crossing2.xml"


DRAW_LABELS = False


def draw_scenario(scenario):
    plot_center = scenario.lanelet_network.lanelets[0].left_vertices[0]
    draw_params = {
        "scenario": {"lanelet_network": {"lanelet": {"show_label": DRAW_LABELS}}}
    }
    plt.style.use("classic")
    plt.figure(figsize=(10, 10))
    plt.gca().axis("equal")
    plot_displacement_x = plot_displacement_y = 200
    plot_limits = [
        plot_center[0] - plot_displacement_x,
        plot_center[0] + plot_displacement_x,
        plot_center[1] - plot_displacement_y,
        plot_center[1] + plot_displacement_y,
    ]
    draw_object(scenario, plot_limits=plot_limits, draw_params=draw_params)
    plt.show()


def convert_to_graph(file: str, accepted_ways, custom_bounds=None, crossing_nodes=[]):
    print("reading File")
    (roads, points, restrictions, center_point, bounds, traffic_signs,
        traffic_lights) = osm_parser.parse_file(
            file, accepted_ways, config.REJECTED_TAGS, custom_bounds
    )
    print("creating graph")
    graph = osm_parser.roads_to_graph(
        roads, points, restrictions, center_point, bounds, center_point,
        traffic_signs, traffic_lights, crossing_nodes
    )
    return graph


def convert_to_intermediate(graph):
    if config.MAKE_CONTIGUOUS:
        print("making graph contiguously")
        graph.make_contiguous()
    print("merging close intersections")
    intersection_merger.merge_close_intersections(graph)
    graph.link_edges()
    graph = Scenario.step_collection_2(graph)
    graph = Scenario.step_collection_3(graph)
    return IntermediateFormat.extract_from_road_graph(graph)


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


# create road/path networks
all_highways = config.ACCEPTED_HIGHWAYS.copy()
all_highways.extend(config.ACCEPTED_PATHWAYS)
combined_graph = convert_to_graph(scenario_file, all_highways)
road_graph = convert_to_graph(scenario_file, config.ACCEPTED_HIGHWAYS,
    combined_graph.bounds)
path_graph = convert_to_graph(scenario_file, config.ACCEPTED_PATHWAYS,
    combined_graph.bounds)
    
# get crossing points
crossing_nodes = []
for candidate_node in combined_graph.nodes:
    is_contained = False
    for node in road_graph.nodes:
        is_contained |= node.id == candidate_node.id
    for node in path_graph.nodes:
        is_contained |= node.id == candidate_node.id
    if not is_contained and not is_close_to_intersection(candidate_node):
        # remove all information about edges from earlier linking
        candidate_node.edges.clear()
        candidate_node.is_crossing = True
        crossing_nodes.append(candidate_node)

# recreate the road graph with the crossing nodes
road_graph = convert_to_graph(scenario_file, config.ACCEPTED_HIGHWAYS,
    combined_graph.bounds, crossing_nodes)

# create intermediate format for road and path network
interm_road = convert_to_intermediate(road_graph)
temp_intersec_dist = config.INTERSECTION_DISTANCE
config.INTERSECTION_DISTANCE = 2.0
interm_path = convert_to_intermediate(path_graph)
config.INTERSECTION_DISTANCE = temp_intersec_dist

# create scenarios
path_scenario = interm_path.to_commonroad_scenario()
draw_scenario(path_scenario)
road_scenario = interm_road.to_commonroad_scenario()
draw_scenario(road_scenario)

# merge networks 
interm_road.nodes.extend(interm_path.nodes)
interm_road.edges.extend(interm_path.edges)
interm_road.traffic_signs.extend(interm_path.traffic_signs)
interm_road.traffic_lights.extend(interm_path.traffic_lights)
interm_road.obstacles.extend(interm_path.obstacles)
# interm_road.intersections.extend(interm_path.intersections) intersections only for roads
interm_merged = IntermediateFormat(
    interm_road.nodes,
    interm_road.edges,
    interm_road.traffic_signs,
    interm_road.traffic_lights,
    interm_road.obstacles,
    interm_road.intersections
)

# TODO performance: close if distance < config.intersetion_distance
def is_close_to_crossing(lanelet):
    return True

# find intersecting crossings at existing intersections
crossings = []
for path_lane in path_scenario.lanelet_network.lanelets:
    if is_close_to_crossing(path_lane):
        lanelet_polygon = path_lane.convert_to_polygon()
        intersected_road_ids = road_scenario.lanelet_network.find_lanelet_by_shape(
            lanelet_polygon)
        if intersected_road_ids:
            crossings.append((path_lane.lanelet_id, intersected_road_ids))
            print("path", path_lane.lanelet_id, "crossing", intersected_road_ids)


# integrate crossings to existing intersections
new_crossings = []
for path_id, road_ids in crossings:
    for intersection in interm_merged.intersections:
        incomings_successors = []
        for incoming in intersection.incomings:
            incomings_successors.extend(incoming.successors_left)
            incomings_successors.extend(incoming.successors_straight)
            incomings_successors.extend(incoming.successors_right)
        if set(road_ids) & set(incomings_successors):
            intersection.crossings.add(path_id)
            print("added path", path_id, "to intersection", intersection.intersection_id)
        # raods that are not part of an intersection
        not_part = set(road_ids) - set(incomings_successors)
        if not_part:
            new_crossings.append((path_id, not_part))


# write scenario to file
scenario_merged = interm_merged.to_commonroad_scenario()
cleanup.sanitize(scenario_merged)
draw_scenario(scenario_merged)
planning_prob = interm_merged.get_dummy_planning_problem_set()
author = config.AUTHOR
affiliation = config.AFFILIATION
source = config.SOURCE
tags = export.create_tags(config.TAGS)
cr_writer = file_writer.CommonRoadFileWriter(scenario_merged, planning_prob,
    author, affiliation, source=source, tags=tags)
cr_writer.write_scenario_to_file(target_file, file_writer.OverwriteExistingFile.ALWAYS)
print("Wrote to", target_file)

# integration concepts:
# - difficult to integrate -> let as script
# - subclass of Graph: multilayered graph: has pedestrian layer
# - 

# Facts
# extra information has to be extracted from OSM: 
#   - crossing node positions
# no connection raods between paths and roads
# 

# problems: 
# - some crossings will be added: polygon intersection close to intersections
#   -> only use valid OSM content and make every overlapping a crossing 
#   !!! no couls be valid AND not crossing (bridge)
# - road network will be modified -> is a completely different map 
#   -> can be fixed, but other concept
# - need comparison of graph, intermediate format and scenario while building new combined scenario
#   - graph for crossing nodes
#   - intermediate for merging
#   - scenario for polygon intersection
# where insert the new intersections

# Solution:
# - extra functionality to merge lanelet networks: with specified offset
# - 
 