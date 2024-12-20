import os
import uuid

import numpy as np
from commonroad.visualization.mp_renderer import MPRenderer
from lxml import etree

from crdesigner.common.file_reader import CRDesignerFileReader
from crdesigner.common.file_writer import CRDesignerFileWriter, OverwriteExistingFile
from crdesigner.common.sumo_available import SUMO_AVAILABLE
from crdesigner.map_conversion.map_conversion_interface import commonroad_to_sumo

if SUMO_AVAILABLE:
    from sumocr.interface.sumo_simulation import SumoSimulation
    from sumocr.visualization.video import create_video

    from crdesigner.map_conversion.sumo_map.config import SumoConfig
    from crdesigner.map_conversion.sumo_map.cr2sumo.converter import CR2SumoMapConverter


output_folder = ""  # replace empty string
scenario_name = ""  # replace empty string
input_file = os.path.join(output_folder, scenario_name + ".xml")

scenario, planning_problem = CRDesignerFileReader(input_file).open()

# ----------------------------------------------- Option 1: General API ------------------------------------------------
commonroad_to_sumo(input_file, output_folder)

# ------------------------------------------ Option 2: SUMO conversion APIs --------------------------------------------
try:
    commonroad_reader = CRDesignerFileReader(input_file)
    scenario, _ = commonroad_reader.open()
except etree.XMLSyntaxError as xml_error:
    print(f"SyntaxError: {xml_error}")
    print("There was an error during the loading of the selected CommonRoad file.\n")

if SUMO_AVAILABLE:
    config = SumoConfig.from_scenario_name(str(uuid.uuid4()))
    config.scenario_name = scenario_name
    converter = CR2SumoMapConverter(scenario, config)
    converter.create_sumo_files(output_folder)

# -------------------- Option 3: SUMO conversion APIs with Traffic Simulation and Video Creation -----------------------

# translate scenario to center
centroid = np.mean(
    np.concatenate([la.center_vertices for la in scenario.lanelet_network.lanelets]), axis=0
)
scenario.translate_rotate(-centroid, 0)
planning_problem.translate_rotate(-centroid, 0)

config = SumoConfig.from_scenario_name(scenario_name)

# convert CR to sumo net
wrapper = CR2SumoMapConverter(scenario, config)
wrapper.create_sumo_files(output_folder)
tls_lanelet_id = 43513
traffic_light_system_generated = wrapper.auto_generate_traffic_light_system(tls_lanelet_id)

print(f"Generated Traffic Light System at {tls_lanelet_id}, {traffic_light_system_generated}")

# draw scenario after traffic light generation
rnd = MPRenderer()
wrapper.lanelet_network.draw(rnd)
rnd.render(show=True)

# write generated traffic lights back to CommonRoad file
scenario.r = wrapper.lanelet_network

# run Simulation
simulation = SumoSimulation()
simulation.initialize(config, wrapper)

for t in range(config.simulation_steps):
    simulation.simulate_step()

simulation.stop()

# save resulting scenario
simulated_scenario = simulation.commonroad_scenarios_all_time_steps()
CRDesignerFileWriter(
    simulated_scenario,
    planning_problem,
    author=scenario.author,
    affiliation=scenario.affiliation,
    source=scenario.source,
    tags=scenario.tags,
    location=scenario.location,
).write_scenario_to_file(
    os.path.join(output_folder, config.scenario_name + ".simulated.xml"),
    overwrite_existing_file=OverwriteExistingFile.ALWAYS,
)

print("creating video (this may take some time)")
create_video(
    simulation.commonroad_scenarios_all_time_steps(),
    output_folder,
    trajectory_pred=simulation.ego_vehicles,
)
