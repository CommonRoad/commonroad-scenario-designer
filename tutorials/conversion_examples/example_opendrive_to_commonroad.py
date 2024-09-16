import os
from pathlib import Path

from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.scenario import Tag

from crdesigner.common.config.opendrive_config import open_drive_config
from crdesigner.common.file_writer import CRDesignerFileWriter, OverwriteExistingFile
from crdesigner.map_conversion.map_conversion_interface import opendrive_to_commonroad

input_path = Path("/home/sebastian/Downloads/Town01.xodr")
output_path = Path("/home/sebastian/Downloads/Town01.xml")

config = open_drive_config
config.lanelet_types_backwards_compatible = False
config.proj_string_odr = None

# load OpenDRIVE file, parse it, and convert it to a CommonRoad scenario
scenario = opendrive_to_commonroad(input_path)

# store converted file as CommonRoad scenario
writer = CRDesignerFileWriter(
    scenario=scenario,
    planning_problem_set=PlanningProblemSet(),
    author="Sebastian Maierhofer",
    affiliation="Technical University of Munich",
    source="CommonRoad Scenario Designer",
    tags={Tag.URBAN},
)

# create a folder for the example file if it does not exist
if os.path.exists(Path.cwd() / "example_files") is False:
    os.mkdir(Path.cwd() / "example_files")
if os.path.exists(Path.cwd() / "example_files/opendrive") is False:
    os.mkdir(Path.cwd() / "example_files/opendrive")

writer.write_to_file(str(output_path), OverwriteExistingFile.ALWAYS)
