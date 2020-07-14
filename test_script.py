from PyQt5.QtWidgets import QApplication
import sys

from crmapconverter.osm2cr.converter_modules import converter
from crmapconverter.osm2cr import config
from crmapconverter.io import viewer
from crmapconverter.osm2cr.converter_modules.cr_operations import export

# convert("../Maps/mittlerer_Ring.osm")

source_folder = "test/osm_xml_test_files/"
target_folder = "test_ouput/"
# intersect_and_crossing3, mittlerer_Ring, garching_kreuzung_fixed
file_name = "intersection_and_crossing"

config.EXTRACT_SUBLAYER = True
graph_scen = converter.GraphScenario(source_folder + file_name + ".osm")
# graph_scen.plot()
# graph_scen.save_as_cr(target_folder + file_name + ".xml")


app = QApplication(sys.argv)
main_window = viewer.MainWindow()
_, scenario = export.create_scenario2(graph_scen.graph)
main_window.openScenario(scenario)
sys.exit(app.exec_())
