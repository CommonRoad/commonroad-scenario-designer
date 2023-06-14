import os
from commonroad.scenario.scenario import Tag
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet
from crdesigner.map_conversion.opendrive.opendrive_parser.parser import parse_opendrive
from crdesigner.map_conversion.opendrive.opendrive_conversion.network import Network
from crdesigner.map_conversion.map_conversion_interface import opendrive_to_commonroad
from crdesigner.config.config import OpenDRIVEConversionParams

input_path = "/home/sebastian/Downloads/location1_new.xodr"  # replace empty string
config = OpenDRIVEConversionParams()
config.lanelet_types_backwards_compatible = False

# ----------------------------------------------- Option 1: General API ------------------------------------------------
# load OpenDRIVE file, parse it, and convert it to a CommonRoad scenario

scenario = opendrive_to_commonroad(input_path)
