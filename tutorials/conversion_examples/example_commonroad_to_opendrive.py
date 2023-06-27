import os

from crdesigner.map_conversion.map_conversion_interface import commonroad_to_opendrive
from crdesigner.map_conversion.opendrive.cr_to_opendrive.dataloader import DataLoader
from crdesigner.map_conversion.opendrive.cr_to_opendrive.converter import Converter

scenario_name = "ZAM_Test-1_1_T-1"  # replace empty string
input_folder = "/media/sebastian/TUM/06_code/internal/commonroad-io/tutorials/examples"
# replace empty string
output_folder = ""  # replace empty string
input_file = os.path.join(input_folder, scenario_name + '.xml')
output_file = os.path.join(output_folder, scenario_name + '.xodr')

# ----------------------------------------------- Option 1: General API ------------------------------------------------
commonroad_to_opendrive(input_file, output_file)


# --------------------------------------- Option 2: CR2OpenDRIVE conversion APIs ---------------------------------------

# load the xml file and preprocess it
# data = DataLoader(input_file)
#
# scenario, successors, ids = data.initialize()
# converter = Converter(input_file, scenario, successors, ids)
# converter.convert(output_file)
