"""
This module provides an example of how theavailable methods of the crmapconverter.osm2cr.converter_modules package
can be used.
"""
import crdesigner.osm2cr.converter_modules.converter as converter
import crdesigner.osm2cr.converter_modules.cr_operations.export as ex
from crdesigner.osm2cr import config
from crdesigner.osm2cr.converter_modules.osm_operations.downloader import download_around_map

# download a map
# download_around_map(config.BENCHMARK_ID + '_downloaded.osm', 48.140289, 11.566272)

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
