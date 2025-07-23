import os
import logging
logging.basicConfig(level=logging.DEBUG)
from crdesigner.common.file_reader import CRDesignerFileReader
from crdesigner.verification_repairing.map_verification_repairing import (
    verify_and_repair_dir_maps,
    verify_and_repair_map,
)
from crdesigner.verification_repairing.config import MapVerParams            # config class
from crdesigner.verification_repairing.verification.hol.formula_manager import FormulaManager

logging.basicConfig(level=logging.INFO)
# path to multiple selected (.xml) files
#files = os.path.join(os.getcwd(), "../tests/map_verification/test_maps/")


## files = Path(__file__).resolve().parent / "/tests/map_verification/test_maps/"
## verify_and_repair_dir_maps(files.resolve())
# calling the function on selected (.xml) files
#verify_and_repair_dir_maps(files)

# path to one single file
file = os.path.join(
    #os.getcwd(), "tests/map_verification/test_maps/merging_lanelets_utm_3d.xml"
    #os.getcwd(), "tests/map_verification/test_maps/Town15CrdWithZ.xml"
    #os.getcwd(), "tests/map_verification/test_maps/paper_test_maps/DEU_BadEssen-3_1_T-1.xml"
    os.getcwd(), "/home/yu/Desktop/commonroad-scenario-designer/example_files/opendrive/opendrive-1.xml"

)
# reading that (.pb) file.
scenario, _ = CRDesignerFileReader(file).open()
fm = FormulaManager(lanelet_network=scenario.lanelet_network)  

# ────────────────── create  ──────────────────
cfg = MapVerParams()                    # get default config
cfg.verification.formula_manager = fm   # replace default with own formula manager
# calling the function on single lanelet network
#verify_and_repair_map(scenario.lanelet_network, scenario_id=scenario.scenario_id)
net, result = verify_and_repair_map(scenario.lanelet_network,
                                    scenario_id=scenario.scenario_id,config=cfg)

#logging.info("%s", result)
