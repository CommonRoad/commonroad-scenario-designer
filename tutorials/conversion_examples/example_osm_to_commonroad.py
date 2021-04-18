import os

from crdesigner.io.api import osm_to_commonroad

from commonroad.scenario.scenario import Tag
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet

import crdesigner.conversion.osm2cr.converter_modules.converter as converter
import crdesigner.conversion.osm2cr.converter_modules.cr_operations.export as ex
from crdesigner.conversion.osm2cr import config
from crdesigner.conversion.osm2cr.converter_modules.osm_operations.downloader import download_around_map

# download a map
download_around_map(config.BENCHMARK_ID + '_downloaded.osm', 48.140289, 11.566272)

# ----------------------------------------------- Option 1: General API ------------------------------------------------
# load OpenDRIVE file, parse it, and convert it to a CommonRoad scenario
scenario = osm_to_commonroad(config.SAVE_PATH + config.BENCHMARK_ID + ".osm")

# store converted file as CommonRoad scenario
writer = CommonRoadFileWriter(
    scenario=scenario,
    planning_problem_set=PlanningProblemSet(),
    author="Sebastian Maierhofer",
    affiliation="Technical University of Munich",
    source="CommonRoad Scenario Designer",
    tags={Tag.URBAN},
)
writer.write_to_file(os.path.dirname(os.path.realpath(__file__)) + "/" + "ZAM_OSM-1_1-T1.xml",
                     OverwriteExistingFile.ALWAYS)


# ----------------------------------------- Option 2: OSM conversion APIs ----------------------------------------------

# open the map and convert it to a scenario
scenario = converter.GraphScenario(config.SAVE_PATH + config.BENCHMARK_ID + ".osm")

# draw and show the scenario
scenario.plot()

# save the scenario as commonroad file
scenario.save_as_cr(config.SAVE_PATH + config.BENCHMARK_ID + ".xml")
# save the scenario as a binary
scenario.save_to_file(config.SAVE_PATH + config.BENCHMARK_ID + ".pickle")

# view the generated
ex.view_xml(config.SAVE_PATH + config.BENCHMARK_ID + ".xml")
