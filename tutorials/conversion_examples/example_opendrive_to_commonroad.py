import os
from pathlib import Path

from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.scenario import Tag

from crdesigner.common.config.opendrive_config import open_drive_config
from crdesigner.common.file_writer import CRDesignerFileWriter, OverwriteExistingFile
from crdesigner.map_conversion.map_conversion_interface import opendrive_to_commonroad

#input_path = Path("/home/sebastian/Downloads/Birmingham_sample_1218.xodr/Birmingham_sample_1218.xodr")
input_path = Path.cwd().parent / "conversion_examples/with_bug.xodr"

output_path = Path.cwd() / "example_files/opendrive/birmingham.xml"

config = open_drive_config
config.lanelet_types_backwards_compatible = False

# load OpenDRIVE file, parse it, and convert it to a CommonRoad scenario
scenario = opendrive_to_commonroad(input_path)

import matplotlib.pyplot as plt
from commonroad.visualization.mp_renderer import MPRenderer

# plot the planning problem and the scenario for the fifth time step
plt.figure(figsize=(25, 10))
rnd = MPRenderer()
scenario.draw(rnd)
rnd.render()
plt.show()
