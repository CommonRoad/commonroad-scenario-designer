from lxml import etree
import os

from commonroad.scenario.scenario import Tag
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet

from crdesigner.map_conversion.lanelet_lanelet2.lanelet2cr import Lanelet2CRConverter
from crdesigner.map_conversion.lanelet_lanelet2.lanelet2_parser import Lanelet2Parser

from crdesigner.map_conversion.map_conversion_interface import lanelet_to_commonroad

input_path = ""  # replace empty string
proj = ""  # replace empty string
left_driving = False  # replace with favoured value
adjacencies = False  # replace with favoured value

# ----------------------------------------------- Option 1: General API ------------------------------------------------
# load lanelet/lanelet2 file, parse it, and convert it to a CommonRoad scenario
scenario = lanelet_to_commonroad(input_path, proj, left_driving, adjacencies)

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
parser = Lanelet2Parser(etree.parse(input_path).getroot())
lanelet2_content = parser.parse()

# convert lanelet/lanelet2 map to CommonRoad
lanelet2_converter = Lanelet2CRConverter(proj_string=proj)
scenario = lanelet2_converter(lanelet2_content, detect_adjacencies=adjacencies, left_driving_system=left_driving)

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
