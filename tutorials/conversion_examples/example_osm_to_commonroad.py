import os
from pathlib import Path

from crdesigner.map_conversion.map_conversion_interface import osm_to_commonroad

from commonroad.scenario.scenario import Tag
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet


# load OpenDRIVE file, parse it, and convert it to a CommonRoad scenario
scenario = osm_to_commonroad(str(Path.cwd().parent.parent/"tests/map_conversion/test_maps/osm/munich.osm"))

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
if os.path.exists(Path.cwd()/"example_files/osm") is False:
    os.mkdir(Path.cwd()/"example_files/osm")

writer.write_to_file(str(Path.cwd()/"example_files/osm/munich.xml"), OverwriteExistingFile.ALWAYS)
