import os

from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.scenario import Tag

from crdesigner.map_conversion.map_conversion_interface import osm_to_commonroad_using_sumo

# ----------------- Manual Step -----------------
# Go to https://www.openstreetmap.org/ and click on button "Export" at the top left. You might want to
# change the exported area via "Manually select a different area". The file donautal-west.osm was created like this.

scenario_name = 'donautal-west'
scenario = osm_to_commonroad_using_sumo(f'{scenario_name}.osm')

writer = CommonRoadFileWriter(
    scenario=scenario,
    planning_problem_set=PlanningProblemSet(),
    author="YOUR NAME",
    affiliation="Technical University of Munich",
    source="CommonRoad Scenario Designer",
    tags={Tag.URBAN},
)
writer.write_to_file(os.path.dirname(os.path.realpath(__file__)) + "/" + f"{scenario_name}.xml",
                     OverwriteExistingFile.ALWAYS)
