from matplotlib import pyplot as plt

from commonroad.visualization.draw_dispatch_cr import draw_object
from crmapconverter.osm2cr import config
from crmapconverter.osm2cr.converter_modules import converter
from crmapconverter.osm2cr.converter_modules.utility import plots
from crmapconverter.osm2cr.converter_modules.graph_operations import road_graph
from crmapconverter.osm2cr.converter_modules.intermediate_format.intermediate_format import IntermediateFormat

scenario_file = "/home/max/Desktop/Planning/Maps/osm_files/garching_kreuzung.osm"

DRAW_LABELS = True


def draw_scenario(scenario, draw_params, plot_center):
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
intermediate_path =  IntermediateFormat.extract_from_road_graph(
    converter.Scenario(scenario_file).graph
)
print("******paths")

config.ACCEPTED_HIGHWAYS = temp_accepted_highways
config.ACCEPTED_PATHWAYS = []
intermediate_road =  IntermediateFormat.extract_from_road_graph(
    converter.Scenario(scenario_file).graph
)
print("******roads")

# TODO Adjust coordinate offset

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


plot_center = scenario_merged.lanelet_network.lanelets[0].left_vertices[0]
draw_scenario(scenario_merged, draw_params, plot_center)

