from matplotlib import pyplot as plt
import numpy as np

from commonroad.visualization.draw_dispatch_cr import draw_object
from crmapconverter.osm2cr import config
from crmapconverter.osm2cr.converter_modules import converter
from crmapconverter.osm2cr.converter_modules.intermediate_format.intermediate_format import IntermediateFormat
from crmapconverter.osm2cr.converter_modules.utility.geometry import lon_lat_to_cartesian

#scenario_file = "/home/max/Desktop/Planning/Maps/osm_files/garching_kreuzung.osm"
scenario_file = "/home/max/Desktop/Planning/Maps/osm_files/only_straigt_test.osm"

DRAW_LABELS = True

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

temp_accepted_highways = config.ACCEPTED_HIGHWAYS
config.ACCEPTED_HIGHWAYS = []
path_graph = converter.Scenario(scenario_file).graph
intermediate_path = IntermediateFormat.extract_from_road_graph(path_graph)
print("******paths")
path_scenario = intermediate_path.to_commonroad_scenario()
plot_center = path_scenario.lanelet_network.lanelets[0].left_vertices[0]
draw_scenario(path_scenario, plot_center)

config.ACCEPTED_HIGHWAYS = temp_accepted_highways
config.ACCEPTED_PATHWAYS = []

# TODO use custom bounds
road_graph = converter.Scenario(scenario_file).graph


intermediate_road =  IntermediateFormat.extract_from_road_graph(road_graph)
print("******roads")
road_scenario = intermediate_road.to_commonroad_scenario()
plot_center = road_scenario.lanelet_network.lanelets[0].left_vertices[0]
draw_scenario(road_scenario, plot_center)

# Adjust coordinate offset of path scenario
path_offset = np.array(lon_lat_to_cartesian(
    np.array(road_graph.center_point),
    np.array(path_graph.center_point)
))

# move node positions
nodes_to_move = []
nodes_to_move.extend(intermediate_path.nodes)
for e in intermediate_path.edges:
    nodes_to_move.append(e.node1)
    nodes_to_move.append(e.node2)
print("to move:", sorted([int(p.id) for p in nodes_to_move]))
for n in nodes_to_move:
    n.point.x -= path_offset[0]
    n.point.y -= path_offset[1]

# move edge points
points_to_move = []

def contains(p_ref):
    for p in points_to_move:
        if p_ref is p:
            return True
    return False

for e in intermediate_path.edges:
    for point in e.left_bound:
        if not contains(point):
            points_to_move.append(point)
    for point in e.center_points:
        if not contains(point):
            points_to_move.append(point)
    for point in e.right_bound:
        if not contains(point):
            points_to_move.append(point)
for point in points_to_move:
    point[0] -= path_offset[0]
    point[1] -= path_offset[1]

assert not intermediate_path.obstacles, "obstacle mapping not implemented"
for traffic_light in intermediate_path.traffic_lights:
    if not (traffic_light._position is None):
        traffic_light._position -= path_offset
for traffic_sign in intermediate_path.traffic_signs:
    if not (traffic_sign._position is None):
        traffic_sign._position -= path_offset

# merge networks
intermediate_path.nodes.extend(intermediate_road.nodes)
intermediate_path.edges.extend(intermediate_road.edges)
intermediate_path.traffic_signs.extend(intermediate_road.traffic_signs)
intermediate_path.traffic_lights.extend(intermediate_road.traffic_lights)
intermediate_path.obstacles.extend(intermediate_road.obstacles)
intermediate_path.intersections.extend(intermediate_road.intersections)
merged = IntermediateFormat(
    intermediate_path.nodes,
    intermediate_path.edges,
    intermediate_path.traffic_signs,
    intermediate_path.traffic_lights,
    intermediate_path.obstacles,
    intermediate_path.intersections
)

# TODO find crossings

scenario_merged = merged.to_commonroad_scenario()

# draw scenario

plot_center = scenario_merged.lanelet_network.lanelets[0].left_vertices[0]
draw_scenario(scenario_merged, plot_center)



