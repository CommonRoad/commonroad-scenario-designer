# -*- coding: utf-8 -*-

"""Module to execute the Qt Program for a GUI conversion."""

import os
import signal
import sys

from lxml import etree

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QFileDialog, QMainWindow
from PyQt5.QtWidgets import (
    QPushButton,
    QMessageBox,
    QLabel,
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QRadioButton,
)

from commonroad.common.file_writer import CommonRoadFileWriter
from commonroad.common.file_reader import CommonRoadFileReader

from crmapconverter.osm.osm2lanelet import OSM2LConverter
from crmapconverter.osm.parser import OSMParser
from crmapconverter.osm.lanelet2osm import L2OSMConverter

from crmapconverter.opendriveparser.parser import parse_opendrive
from crmapconverter.opendriveconversion.network import Network
from crmapconverter.io.viewer import MainWindow as ViewerWidget

try:
    from crmapconverter.osm2cr.main import start_gui
except ModuleNotFoundError as module_err:
    print(module_err)
    print("It seems like you did not install the dependencies for osm2cr.")

__author__ = "Benjamin Orthen, Stefan Urban, Sebastian Maierhofer"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "1.2.0"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad-i06@in.tum.de"
__status__ = "Released"


class OSMLaneletsConvertWindow(QWidget):
    """Window for conversion between OSM and CommonRoad lanelets."""

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.loaded_osm = None
        self.loaded_scenario = None

        self._init_user_interface()
        self.show()

    def _init_user_interface(self):
        """Build the user interface."""

        self.setWindowTitle("Lanelets CommonRoad <-> OSM Converter")

        # self.setFixedSize(560, 345)

        form_layout = QFormLayout(self)

        self.load_button = QPushButton("Load file", self)
        self.load_button.setToolTip("Load a Lanelets map")
        # self.load_button.move(10, 10)
        # self.load_button.resize(130, 35)
        self.load_button.clicked.connect(self.open_file_dialog)

        self.input_file = QLineEdit(self)
        # self.input_file.move(150, 10)
        # self.input_file.resize(400, 35)
        self.input_file.setReadOnly(True)
        form_layout.addRow(self.load_button, self.input_file)

        self.proj_string_line = QLineEdit(self)
        # self.proj_string_line.move(150, 100)
        # self.proj_string_line.resize(400, 35)
        form_layout.addRow(QLabel("Proj-string"), self.proj_string_line)

        self.direction_checkbox = QCheckBox("Use file ending")
        self.direction_checkbox.setChecked(True)
        # self.direction_checkbox.move(150, 150)
        form_layout.addRow(
            QLabel("Method to detect conversion direction"), self.direction_checkbox
        )
        self.export_to_cr_file = QPushButton("Export as CommonRoad", self)
        # self.export_to_cr_file.move(200, 300)
        # self.export_to_cr_file.resize(170, 35)
        self.export_to_cr_file.setDisabled(True)
        self.export_to_cr_file.clicked.connect(self.export_as_commonroad)

        self.export_to_osm_file = QPushButton("Export as OSM", self)
        # self.export_to_osm_file.move(10, 300)
        # self.export_to_osm_file.resize(170, 35)
        self.export_to_osm_file.setDisabled(True)
        self.export_to_osm_file.clicked.connect(self.export_as_osm)
        export_button_qhbox = QHBoxLayout(self)
        export_button_qhbox.addWidget(self.export_to_cr_file)
        export_button_qhbox.addWidget(self.export_to_osm_file)

        conversion_direction_hbox = QHBoxLayout()
        self.osm_to_cr_button = QRadioButton("OSM to CR")
        self.cr_to_osm_button = QRadioButton("CR to OSM")
        conversion_direction_hbox.addWidget(self.osm_to_cr_button)
        conversion_direction_hbox.addWidget(self.cr_to_osm_button)
        form_layout.addRow(QLabel("Conversion direction"), conversion_direction_hbox)

        self.status_qlabel = QLabel("")
        form_layout.addRow(QLabel("Status:"), self.status_qlabel)
        form_layout.addRow(export_button_qhbox)

        # self.viewOutputButton = QPushButton("View Road Network", self)
        # self.viewOutputButton.move(190, 300)
        # self.viewOutputButton.resize(170, 35)
        # self.viewOutputButton.setDisabled(True)

    def reset_output_elements(self):
        """"""
        self.export_to_cr_file.setDisabled(True)
        self.export_to_osm_file.setDisabled(True)
        self.loaded_osm = None
        self.loaded_scenario = None
        self.set_status("")

    def set_status(self, text):
        self.status_qlabel.setText(text)

    def open_file_dialog(self):
        """"""
        self.reset_output_elements()

        path, _ = QFileDialog.getOpenFileName(
            self,
            "QFileDialog.getOpenFileName()",
            "",
            "Lanelet map files (*.osm *.xml)",
            options=QFileDialog.Options(),
        )

        if not path:
            return

        filename = os.path.basename(path)
        self.input_file.setText(filename)

        if self.direction_checkbox.isChecked():
            file_ending = path.rpartition(".")[2]
            if file_ending == "osm":
                self.osm_to_cr_button.setChecked(True)
            elif file_ending == "xml":
                self.cr_to_osm_button.setChecked(True)

        if self.osm_to_cr_button.isChecked():
            with open(path) as file_in:
                parser = OSMParser(etree.parse(file_in).getroot())
            self.loaded_osm = parser.parse()
            self.export_to_cr_file.setDisabled(False)

        elif self.cr_to_osm_button.isChecked():
            try:
                commonroad_reader = CommonRoadFileReader(path)
                self.loaded_scenario, _ = commonroad_reader.open()
                self.export_to_osm_file.setDisabled(False)

            except (etree.XMLSyntaxError, AssertionError) as err:
                print(f"SyntaxError: {err}")
                self.set_status(
                    "There was an error during the loading of the selected CommonRoad file.\n"
                )

        if self.loaded_scenario or self.loaded_osm:
            self.set_status("Loaded file.")

    def export_as_commonroad(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "QFileDialog.getSaveFileName()",
            "",
            "CommonRoad files (*.xml)",
            options=QFileDialog.Options(),
        )
        if not file_path:
            return
        if not file_path.endswith(".xml"):
            file_path += ".xml"

        self.set_status("Converting.")
        osm2l = OSM2LConverter(proj_string=self.proj_string_line.text())
        scenario = osm2l(self.loaded_osm)
        if scenario:
            writer = CommonRoadFileWriter(
                scenario=scenario,
                planning_problem_set=None,
                author="",
                affiliation="",
                source="OSM 2 CommonRoad Converter",
                tags="",
            )
            with open(f"{file_path}", "w") as file_out:
                writer.write_scenario_to_file_io(file_out)

        else:
            print("Could not convert from OSM to CommonRoad format!")

        self.set_status("Finished.")

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
