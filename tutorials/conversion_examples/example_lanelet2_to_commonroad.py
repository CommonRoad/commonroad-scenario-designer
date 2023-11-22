from pathlib import Path

from lxml import etree
import os

from commonroad.scenario.scenario import Tag
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet

from crdesigner.config.lanelet2_config import lanelet2_config
from crdesigner.map_conversion.map_conversion_interface import lanelet_to_commonroad

input_path = Path.cwd().parent.parent/"tests/map_conversion/test_maps/lanelet2/merging_lanelets_utm.osm"
output_path = Path.cwd()/"example_files/lanelet2/merging_lanelets_utm.xml"

lanelet2_config.adjacencies = True

# load lanelet/lanelet2 file, parse it, and convert it to a CommonRoad scenario
scenario = lanelet_to_commonroad(str(input_path))

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
if os.path.exists(Path.cwd()/"example_files/lanelet2") is False:
    os.mkdir(Path.cwd()/"example_files/lanelet2")

writer.write_to_file(str(output_path), OverwriteExistingFile.ALWAYS)
