import os

from crdesigner.map_conversion.map_conversion_interface import sumo_to_commonroad

from commonroad.scenario.scenario import Tag
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet

from crdesigner.ui.gui.utilities.gui_sumo_simulation import SUMO_AVAILABLE
if SUMO_AVAILABLE:
    from crdesigner.map_conversion.sumo_map.sumo2cr import convert_net_to_cr

input_file = ""  # replace empty string

# ----------------------------------------------- Option 1: General API ------------------------------------------------
# load SUMO net file, parse it, and convert it to a CommonRoad map
scenario = sumo_to_commonroad(input_file)

# store converted file as CommonRoad scenario
writer = CommonRoadFileWriter(
    scenario=scenario,
    planning_problem_set=PlanningProblemSet(),
    author="Sebastian Maierhofer",
    affiliation="Technical University of Munich",
    source="CommonRoad Scenario Designer",
    tags={Tag.URBAN},
)
writer.write_to_file(os.path.dirname(os.path.realpath(__file__)) + "/" + "ZAM_SUMO-1_1-T1.xml",
                     OverwriteExistingFile.ALWAYS)


# ---------------------------------------- Option 2: SUMO conversion APIs ----------------------------------------------

# load SUMO net file, parse it, and convert it to a CommonRoad map
scenario = convert_net_to_cr(input_file)

# store converted file as CommonRoad scenario
writer = CommonRoadFileWriter(
    scenario=scenario,
    planning_problem_set=PlanningProblemSet(),
    author="Sebastian Maierhofer",
    affiliation="Technical University of Munich",
    source="CommonRoad Scenario Designer",
    tags={Tag.URBAN},
)
writer.write_to_file(os.path.dirname(os.path.realpath(__file__)) + "/" + "ZAM_SUMO-1_1-T1.xml",
                     OverwriteExistingFile.ALWAYS)
