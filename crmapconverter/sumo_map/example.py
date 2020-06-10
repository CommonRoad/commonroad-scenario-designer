import os
import numpy as np

from crmapconverter.sumo_map.cr2sumo import CR2SumoMapConverter
from crmapconverter.sumo_map.config import SumoConfig
from commonroad.common.file_reader import CommonRoadFileReader

# from crmapconverter.sumo_map.sumo_interface.sumo2cr.interface.sumo_simulation import SumoSimulation

# path config
files_folder = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'test_files'))
scenario_name = "merging_lanelets_utm"
input_file = os.path.join(files_folder, scenario_name + '.xml')
net_path = os.path.join(files_folder, scenario_name + ".net.xml")

scenario, planning_problem = CommonRoadFileReader(input_file).open()

# translate scenario to center
centroid = np.mean(np.concatenate(
    [l.center_vertices for l in scenario.lanelet_network.lanelets]),
                   axis=0)
scenario.translate_rotate(-centroid, 0)
planning_problem.translate_rotate(-centroid, 0)

config = SumoConfig()
# convert net to .net.xml
scenario = CR2SumoMapConverter(scenario.lanelet_network, config)
scenario.convert_to_net_file(net_path)

# # run Simulation
# simulation = SumoSimulation()
# simulation.initialize(config, scenario_wrapper)

# for t in range(config.simulation_steps):
#     simulation.simulate_step()

# simulation.stop()

# # save resulting scenario
# print(simulation.commonroad_scenarios_all_time_steps())
