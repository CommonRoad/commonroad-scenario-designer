import os
from commonroad.common.file_reader import CommonRoadFileReader
from crdesigner.verification_repairing.map_verification_repairing import verify_and_repair_dir_maps, verify_and_repair_map

# path to multiple selected (.xml) files
files = os.path.join(os.getcwd(), '../tests/map_verification/test_maps/')

# calling the function on selected (.xml) files
verify_and_repair_dir_maps(files)

# path to one single file
file = os.path.join(os.getcwd(), '../tests/map_verification/test_maps/paper_test_maps/DEU_BadEssen-3_1_T-1.xml')
# reading that (.pb) file.
scenario, pp = CommonRoadFileReader(file).open()
# calling the function on single lanelet network
verify_and_repair_map(scenario.lanelet_network, scenario_id=scenario.scenario_id)
