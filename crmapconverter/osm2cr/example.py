"""
This module provides an example of how theavailable methods of the converter_modules package can be used.
"""
import converter_modules.converter as converter
import converter_modules.cr_operations.export as ex
import config
from converter_modules.osm_operations.downloader import download_around_map

# download a map
# download_around_map(config.BENCHMARK_ID + '_downloaded.osm', 48.140289, 11.566272)

# open the map and convert it to a scenario
scenario = converter.Scenario(config.SAVE_PATH + config.BENCHMARK_ID + '_downloaded.osm')

# draw and show the scenario
scenario.plot()

# save the scenario as commonroad file
scenario.save_as_cr()
# save the scenario as a binary
scenario.save_to_file(config.SAVE_PATH + config.BENCHMARK_ID + '.pickle')

# view the generated
ex.view_xml(config.SAVE_PATH + config.BENCHMARK_ID + '.xml')
