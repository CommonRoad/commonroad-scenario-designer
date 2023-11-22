import os
from pathlib import Path

from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.scenario import Tag

from crdesigner.map_conversion.map_conversion_interface import osm_to_commonroad_using_sumo
scenario = osm_to_commonroad_using_sumo(str(Path.cwd().parent.parent/"tests/map_conversion/test_maps/osm/ped_crossing.osm"))

writer = CommonRoadFileWriter(
    scenario=scenario,
    planning_problem_set=PlanningProblemSet(),
    author="YOUR NAME",
    affiliation="Technical University of Munich",
    source="CommonRoad Scenario Designer",
    tags={Tag.URBAN},
)

# create a folder for the example file if it does not exist
if os.path.exists(Path.cwd()/"example_files") is False:
    os.mkdir(Path.cwd()/"example_files")
if os.path.exists(Path.cwd()/"example_files/osm") is False:
    os.mkdir(Path.cwd()/"example_files/osm")

writer.write_to_file(str(Path.cwd()/"example_files/osm/test_ped_crossing.xml"), OverwriteExistingFile.ALWAYS)
