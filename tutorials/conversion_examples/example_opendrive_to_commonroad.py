import os
from pathlib import Path
from commonroad.scenario.scenario import Tag
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet

from crdesigner.config.opendrive_config import open_drive_config
from crdesigner.map_conversion.map_conversion_interface import opendrive_to_commonroad

input_path = Path.cwd().parent.parent/"tests/map_conversion/test_maps/opendrive/opendrive-1.xodr"
output_path = Path.cwd()/"example_files/opendrive/opendrive-1.xml"

config = open_drive_config
config.lanelet_types_backwards_compatible = False

# load OpenDRIVE file, parse it, and convert it to a CommonRoad scenario
scenario = opendrive_to_commonroad(input_path)

# store converted file as CommonRoad scenario
writer = CommonRoadFileWriter(
    scenario=scenario,
    planning_problem_set=PlanningProblemSet(),
    author="Sebastian Maierhofer",
    affiliation="Technical University of Munich",
    source="CommonRoad Scenario Designer",
    tags={Tag.URBAN},
)

# create a folder for the example file if it does not exist
if os.path.exists(Path.cwd()/"example_files") is False:
    os.mkdir(Path.cwd()/"example_files")
if os.path.exists(Path.cwd()/"example_files/opendrive") is False:
    os.mkdir(Path.cwd()/"example_files/opendrive")

writer.write_to_file(str(output_path), OverwriteExistingFile.ALWAYS)

