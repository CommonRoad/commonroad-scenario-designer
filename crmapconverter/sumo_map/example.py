import os
import numpy as np

from crmapconverter.sumo_map.cr2sumo import CR2SumoMapConverter
from crmapconverter.sumo_map.config import SumoConfig
from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.file_writer import CommonRoadFileWriter
from commonroad.scenario.scenario import Scenario
from commonroad.visualization.draw_dispatch_cr import draw_object
import matplotlib.pyplot as plt

from sumocr.interface.sumo_simulation import SumoSimulation
from sumocr.visualization.video import create_video

# path config
output_folder = os.path.join(os.path.dirname(__file__), 'test_files')
scenario_name = "intersect_and_crossing"
input_file = os.path.join(output_folder, scenario_name + '.xml')

scenario, planning_problem = CommonRoadFileReader(input_file).open()

# translate scenario to center
centroid = np.mean(np.concatenate(
    [l.center_vertices for l in scenario.lanelet_network.lanelets]),
                   axis=0)
scenario.translate_rotate(-centroid, 0)
planning_problem.translate_rotate(-centroid, 0)

config = SumoConfig.from_scenario_name(scenario_name)

# # convert CR to sumo net
wrapper = CR2SumoMapConverter(scenario.lanelet_network, config)
wrapper.convert_to_net_file(output_folder)
# traffic_light_system_generated = wrapper.auto_generate_traffic_light_system(26, cycle_time=10)

# # draw scenario after traffic light generation
# plt.figure(figsize=(25, 25))
# draw_object(wrapper.lanelet_network)
# plt.axis('equal')
# plt.autoscale()
# plt.show()

# # write generated traffic lights back to commonroad file
# scenario.lanelet_network = wrapper.lanelet_network
# CommonRoadFileWriter(scenario,
#                      planning_problem,
#                      author=scenario.author,
#                      affiliation=scenario.affiliation,
#                      source=scenario.source,
#                      tags=scenario.tags,
#                      location=scenario.location).write_scenario_to_file(
#                          os.path.join(output_folder,
#                                       config.scenario_name + ".xml"),
#                          overwrite_existing_file=True)

# # run Simulation
# simulation = SumoSimulation()
# simulation.initialize(config, wrapper)

# for t in range(config.simulation_steps):
#     simulation.simulate_step()

# simulation.stop()

# # save resulting scenario
# simulated_scenario = simulation.commonroad_scenarios_all_time_steps()
# CommonRoadFileWriter(simulated_scenario,
#                      planning_problem,
#                      author=scenario.author,
#                      affiliation=scenario.affiliation,
#                      source=scenario.source,
#                      tags=scenario.tags,
#                      location=scenario.location).write_scenario_to_file(
#                          os.path.join(output_folder,
#                                       config.scenario_name + ".simulated.xml"),
#                          overwrite_existing_file=True)

# print("creating video (this may take some time)")
# create_video(simulation, 1, config.simulation_steps, output_folder)