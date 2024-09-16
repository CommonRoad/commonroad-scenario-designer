import os
from pathlib import Path

from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.scenario import Tag

from crdesigner.common.config.lanelet2_config import lanelet2_config
from crdesigner.common.file_writer import CRDesignerFileWriter, OverwriteExistingFile
from crdesigner.map_conversion.map_conversion_interface import lanelet_to_commonroad

input_path = Path("/home/sebastian/Downloads/1_cologne_fortiib.osm")
output_path = Path("/home/sebastian/Downloads/1_cologne_fortiib.xml")

lanelet2_config.adjacencies = True

# load lanelet/lanelet2 file, parse it, and convert it to a CommonRoad scenario
scenario = lanelet_to_commonroad(str(input_path))

# store converted file as CommonRoad scenario
writer = CRDesignerFileWriter(
    scenario=scenario,
    planning_problem_set=PlanningProblemSet(),
    author="Sebastian Maierhofer",
    affiliation="Technical University of Munich",
    source="CommonRoad Scenario Designer",
    tags={Tag.URBAN},
)


writer.write_to_file(str(output_path), OverwriteExistingFile.ALWAYS)
