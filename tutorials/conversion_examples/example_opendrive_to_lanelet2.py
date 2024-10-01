import os
from pathlib import Path

from crdesigner.common.config.general_config import general_config
from crdesigner.common.config.lanelet2_config import lanelet2_config
from crdesigner.common.config.opendrive_config import open_drive_config
from crdesigner.map_conversion.map_conversion_interface import opendrive_to_lanelet

# get the input and the output paths
input_path = Path.cwd().parent.parent / "tests/map_conversion/test_maps/odr2cr/opendrive-1.xodr"
output_path = Path.cwd() / "example_files/lanelet2/l2_opendrive-1.osm"

# define configs
opendrive_config = open_drive_config
lanelet2_config = lanelet2_config
general_config = general_config

# create a folder for the example file if it does not exist
if os.path.exists(Path.cwd() / "example_files") is False:
    os.mkdir(Path.cwd() / "example_files")
if os.path.exists(Path.cwd() / "example_files/lanelet2") is False:
    os.mkdir(Path.cwd() / "example_files/lanelet2")

# conversion
opendrive_to_lanelet(
    input_file=input_path,
    output_file=str(output_path),
    odr_config=opendrive_config,
    general_config=general_config,
    lanelet2_config=lanelet2_config,
)
