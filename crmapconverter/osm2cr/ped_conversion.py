from crmapconverter.osm2cr.converter_modules import converter
from crmapconverter.osm2cr.converter_modules.cr_operations import export
from crmapconverter.osm2cr.converter_modules.cr_operations import cleanup
import crmapconverter.io.viewer as viewer
from PyQt5.QtWidgets import QApplication
import sys

source_folder = "/home/max/Desktop/Planning/Maps/osm_files/"
target_folder = "/home/max/Desktop/Planning/Maps/cr_files/"
filename = "karolinenplatz"

print("create scenario")
graph = converter.GraphScenario(source_folder + filename + ".osm").graph

export.export(graph, file_path=target_folder + filename + ".xml")
# scen, _ = export.create_scenario_intermediate(graph)
# cleanup.sanitize(scen)

# Startup application
# print("draw scenario")
# app = QApplication(sys.argv)
# main_win = viewer.MainWindow()
# main_win.openScenario(scen)
# main_win.show()
# sys.exit(app.exec_())
