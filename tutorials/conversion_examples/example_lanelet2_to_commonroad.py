from lxml import etree
import os

from commonroad.scenario.scenario import Tag, ScenarioID
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet

from crdesigner.config.lanelet2_config import lanelet2_config
from crdesigner.map_conversion.lanelet2.lanelet2cr import Lanelet2CRConverter
from crdesigner.map_conversion.lanelet2.lanelet2_parser import Lanelet2Parser

from crdesigner.map_conversion.map_conversion_interface import lanelet_to_commonroad

input_path = ""  # replace empty string
lanelet2_config.adjacencies = True


# ----------------------------------------------- Option 1: General API ------------------------------------------------
# load lanelet/lanelet2 file, parse it, and convert it to a CommonRoad scenario
scenario = lanelet_to_commonroad(input_path)

# store converted file as CommonRoad scenario
writer = CommonRoadFileWriter(
    scenario=scenario,
    planning_problem_set=PlanningProblemSet(),
    author="Sebastian Maierhofer",
    affiliation="Technical University of Munich",
    source="CommonRoad Scenario Designer",
    tags={Tag.URBAN},
)
writer.write_to_file(os.path.dirname(os.path.realpath(__file__)) + "/" + "ZAM_Lanelet-1_1-T1.xml",
                     OverwriteExistingFile.ALWAYS)

# ---------------------------------------- Option 2: Lanelet conversion APIs -------------------------------------------
# read and parse lanelet/lanelet2 file
parser = Lanelet2Parser(etree.parse(input_path).getroot(), lanelet2_config)
lanelet2_content = parser.parse()

# convert lanelet/lanelet2 map to CommonRoad
lanelet2_converter = Lanelet2CRConverter()
scenario = lanelet2_converter(lanelet2_content)
scenario.scenario_id = ScenarioID(country_id="ZAM", map_name="Lanelet")

# store converted file as CommonRoad scenario
writer = CommonRoadFileWriter(
    scenario=scenario,
    planning_problem_set=PlanningProblemSet(),
    author="Sebastian Maierhofer",
    affiliation="Technical University of Munich",
    source="CommonRoad Scenario Designer",
    tags={Tag.URBAN},
)
writer.write_to_file(os.path.dirname(os.path.realpath(__file__)) + "/" + "ZAM_Lanelet-1_1-T1.xml",
                     OverwriteExistingFile.ALWAYS)
