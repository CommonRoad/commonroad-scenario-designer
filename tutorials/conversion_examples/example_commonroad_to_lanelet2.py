import os
from pathlib import Path

from crdesigner.config.lanelet2_config import lanelet2_config
from crdesigner.map_conversion.map_conversion_interface import commonroad_to_lanelet


input_path = Path.cwd().parent.parent/"tests/map_conversion/test_maps/lanelet2/merging_lanelets_utm.xml"
output_name = Path.cwd()/"example_files/lanelet2/merging_lanelets_utm.osm"
config = lanelet2_config
config.autoware = False

# create a folder for the example file if it does not exist
if os.path.exists(Path.cwd()/"example_files") is False:
    os.mkdir(Path.cwd()/"example_files")
if os.path.exists(Path.cwd()/"example_files/lanelet2") is False:
    os.mkdir(Path.cwd()/"example_files/lanelet2")

# load CommonRoad file and convert it to lanelet format
commonroad_to_lanelet(str(input_path), str(output_name), config)
