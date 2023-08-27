import os
from lxml import etree
from commonroad.scenario.scenario import Tag
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet
from crdesigner.map_conversion.map_conversion_interface import opendrive_to_commonroad
from crdesigner.map_conversion.lanelet2.cr2lanelet import CR2LaneletConverter
from crdesigner.config.lanelet2_config import lanelet2_config

input_path = "/home/sebastian/Downloads/Town01.xodr"  # replace empty string
output_name = "/home/sebastian/Downloads/Town01.osm"  # replace empty string

scenario = opendrive_to_commonroad(input_path)
l2osm = CR2LaneletConverter(lanelet2_config)
osm = l2osm(scenario)
with open(f"{output_name}", "wb") as file_out:
    file_out.write(etree.tostring(osm, xml_declaration=True, encoding="UTF-8", pretty_print=True))