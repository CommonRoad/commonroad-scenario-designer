import os
from pathlib import Path

from commonroad_sumo.cr2sumo import CR2SumoMapConverter, SumoTrafficGenerationMode
from commonroad_sumo.simulation import NonInteractiveSumoSimulation
from lxml import etree

from crdesigner.common.file_reader import CRDesignerFileReader
from crdesigner.map_conversion.map_conversion_interface import commonroad_to_sumo

output_folder = Path("")  # replace empty string
scenario_name = ""  # replace empty string
input_file = output_folder / f"{scenario_name}.xml"

scenario, planning_problem = CRDesignerFileReader(input_file).open()

# ----------------------------------------------- Option 1: General API ------------------------------------------------
commonroad_to_sumo(input_file, output_folder)

# ------------------------------------------ Option 2: SUMO conversion APIs --------------------------------------------

converter = CR2SumoMapConverter.from_file(input_file)
converter.create_sumo_files(output_folder)

# -------------------- Option 3: SUMO conversion APIs with Traffic Simulation and Video Creation -----------------------

simulation = NonInteractiveSumoSimulation.from_file(
    input_file, SumoTrafficGenerationMode.SAFE_RESIMULATION
)
simulation_result = simulation.run(simulation_steps=1000)

simulation_result.write_to_folder(output_folder)
