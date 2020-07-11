import sys
from lxml import etree
from PyQt5.QtWidgets import (
    QDialog,
    QWidget,
    QApplication,
    QLineEdit,
    QFormLayout,
    QLabel,
    QPushButton,
    QFileDialog
)

from crmapconverter.osm.lanelet2osm import L2OSMConverter
from crmapconverter.osm2cr.converter_modules.gui_modules.gui_embedding import MainApp
from crmapconverter.osm2cr.converter_modules.cr_operations import export
from crmapconverter.io.V3_0.gui_cr_viewer import CrViewer

class ConverterInterface(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

class OSM_Interface(QDialog):
    """Call OSM converter GUI"""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window

    def start_import(self):
        def pipe_graph_to_GUI(graph):
            scenario, _ = export.convert_to_scenario(graph)
            self.main_window.open_scenario(scenario)

        osm_app = MainApp(self)
        final_action = pipe_graph_to_GUI
        osm_app.start(final_action)

class ExportAsOSMWindow(QWidget):
    """Window for conversion between OSM and CommonRoad lanelets."""

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.loaded_osm = None
        self.loaded_scenario = None
        self._init_user_interface()
        self.show()

    def _init_user_interface(self):
        """Build the user interface."""

        self.setWindowTitle("Export as OSM file")

        form_layout = QFormLayout(self)

        self.proj_string_line = QLineEdit(self)
        form_layout.addRow(QLabel("Proj-string"), self.proj_string_line)

        self.export_to_osm_file = QPushButton("Export as OSM", self)
        self.export_to_osm_file.clicked.connect(self.export_as_osm)
        form_layout.addRow(self.export_to_osm_file)


    def export_as_osm(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "QFileDialog.getSaveFileName()",
            "",
            "OSM files (*.osm)",
            options=QFileDialog.Options(),
        )

        if not path:
            return

        self.set_status("Converting.")
        l2osm = L2OSMConverter(proj_string=self.proj_string_line.text())
        osm = l2osm(self.loaded_scenario)
        with open(f"{path}", "wb") as file_out:
            file_out.write(
                etree.tostring(
                    osm, xml_declaration=True, encoding="UTF-8", pretty_print=True
                )
            )

        self.set_status("Finished.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ExportAsOSMWindow()
    window.show()
    sys.exit(app.exec_())