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


# path to one single file
file = os.path.join(

    os.getcwd(), "/home/yu/Desktop/commonroad-scenario-designer/example_files/opendrive/opendrive-1.xml"

)
# reading that (.pb) file.
scenario, _ = CRDesignerFileReader(file).open()
fm = FormulaManager()  


cfg = MapVerParams()                    # get default config
cfg.verification.formula_manager = fm   # replace default with own formula manager
# calling the function on single lanelet network

net, result = verify_and_repair_map(scenario.lanelet_network,
                                    scenario_id=scenario.scenario_id,config=cfg)

#logging.info("%s", result)
