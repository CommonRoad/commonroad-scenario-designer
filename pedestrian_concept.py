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
target_file = "/home/max/Desktop/Planning/Maps/cr_files/garching_kreuzung_merged.xml"
DRAW_LABELS = False

def draw_scenario(scenario, plot_center):
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

def convert_to_graph(file:str, accepted_highways, custom_bounds=None):
    print("reading File")
    (roads, points, restrictions, center_point, bounds, traffic_signs,
        traffic_lights) = osm_parser.parse_file(
            file, accepted_highways, custom_bounds
    )
    print("creating graph")
    graph = osm_parser.roads_to_graph(
        roads, points, restrictions, center_point, bounds, center_point,
        traffic_signs, traffic_lights
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

# get bounds
all_highways = config.ACCEPTED_HIGHWAYS.copy()
all_highways.extend(config.ACCEPTED_PATHWAYS)
combined_graph = convert_to_graph(scenario_file, all_highways)
combined_bounds = combined_graph.bounds

# get intermediate of road network
road_graph = convert_to_graph(scenario_file, config.ACCEPTED_HIGHWAYS,
    custom_bounds=combined_bounds)
interm_road = convert_to_intermediate(road_graph)
print("******roads")
road_scenario = interm_road.to_commonroad_scenario()
plot_center = road_scenario.lanelet_network.lanelets[0].left_vertices[0]
# draw_scenario(road_scenario, plot_center)

# get intermediate of path network
path_graph = convert_to_graph(scenario_file, config.ACCEPTED_PATHWAYS,
    custom_bounds=combined_bounds)
interm_path = convert_to_intermediate(path_graph)
print("******paths")
path_scenario = interm_path.to_commonroad_scenario()
plot_center = path_scenario.lanelet_network.lanelets[0].left_vertices[0]
# draw_scenario(path_scenario, plot_center)

# TODO find crossing positions
def is_close_to_crossing(lanelet):
    return True

# TODO find crossings
crossings = []
for path_lane in path_scenario.lanelet_network.lanelets:
    if is_close_to_crossing(path_lane):
        poly = path_lane.convert_to_polygon()
        intersected_lanes = road_scenario.lanelet_network.find_lanelet_by_shape(
            poly)
        if intersected_lanes:
            crossings.append((path_lane, intersected_lanes))
            print("path", path_lane.lanelet_id, "crossing", intersected_lanes)

# merge networks
interm_path.nodes.extend(interm_road.nodes)
interm_path.edges.extend(interm_road.edges)
interm_path.traffic_signs.extend(interm_road.traffic_signs)
interm_path.traffic_lights.extend(interm_road.traffic_lights)
interm_path.obstacles.extend(interm_road.obstacles)
interm_path.intersections.extend(interm_road.intersections)
interm_merged = IntermediateFormat(
    interm_path.nodes,
    interm_path.edges,
    interm_path.traffic_signs,
    interm_path.traffic_lights,
    interm_path.obstacles,
    interm_path.intersections
)
scenario_merged = interm_merged.to_commonroad_scenario()

# integrate crossings
# for path_lane

# draw scenario

cleanup.sanitize(scenario_merged)
plot_center = scenario_merged.lanelet_network.lanelets[0].left_vertices[0]
draw_scenario(scenario_merged, plot_center)

planning_prob = interm_merged.get_dummy_planning_problem_set()
author = config.AUTHOR
affiliation = config.AFFILIATION
source = config.SOURCE
tags = export.create_tags(config.TAGS)
cr_writer = file_writer.CommonRoadFileWriter(scenario_merged, planning_prob,
    author, affiliation, source=source, tags=tags)
cr_writer.write_scenario_to_file(target_file, file_writer.OverwriteExistingFile.ALWAYS)