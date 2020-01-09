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

__author__ = "Benjamin Orthen, Stefan Urban"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "1.1.0"
__maintainer__ = "Benjamin Orthen"
__email__ = "commonroad-i06@in.tum.de"
__status__ = "Released"


def main():
    """Execute the gui to convert xodr files and
    visualize commonroad files.

    Args:

    Returns:

    """
    # Make it possible to exit application with ctrl+c on console
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Startup application
    app = QApplication(sys.argv)
    _ = MainWindow()
    sys.exit(app.exec_())


def opendrive_gui():
    """Execute the gui to convert xodr files and
    visualize commonroad files.

    Args:

    Returns:

    """
    # Make it possible to exit application with ctrl+c on console
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Startup application
    app = QApplication(sys.argv)
    _ = OpenDriveConvertWindow(sys.argv)
    sys.exit(app.exec_())


class MainWindow(QWidget):
    """Proper main window"""

    button_y_size = 50
    _button_y_position = 10

    def __init__(self, parent=None):
        super().__init__(parent)

        self._init_user_interface()
        self.show()

    @property
    def _next_button_y_position(self):
        """Get a new position in y direction for a QElement."""
        tmp = self._button_y_position
        self._button_y_position += self.button_y_size
        return tmp

    def make_start_gui(self, parent):
        """start_gui factory"""

        def start_gui_with_parent():
            start_gui(parent)

        return start_gui_with_parent

    def _init_user_interface(self):
        self.setWindowTitle("CommonRoad Map Converter")
        self.setFixedSize(700, 300)

        self.open_opendrive = QPushButton("Convert an OpenDRIVE file to Lanelets", self)
        self.open_opendrive.clicked.connect(self.opendrive_conversion_menu)
        self.open_opendrive.move(10, self._next_button_y_position)
        self.open_opendrive.resize(300, self.button_y_size)

        self.open_cr_visualization = QPushButton("Visualize a CommonRoad map", self)
        self.open_cr_visualization.clicked.connect(self.commonroad_visualization_menu)
        self.open_cr_visualization.move(10, self._next_button_y_position)
        self.open_cr_visualization.resize(300, self.button_y_size)

        self.open_osm2cr = QPushButton("Open OSM2CR conversion tool menu.", self)
        self.open_osm2cr.move(10, self._next_button_y_position)
        self.open_osm2cr.resize(300, self.button_y_size)
        try:
            self.open_osm2cr.clicked.connect(self.make_start_gui(self))
        except NameError:
            self.open_osm2cr.setDisabled(True)

        self.open_osm2cr_lanelets = QPushButton(
            "OSM Lanelets <-> Commonroad Lanelets", self
        )
        self.open_osm2cr_lanelets.move(10, self._next_button_y_position)
        self.open_osm2cr_lanelets.resize(300, self.button_y_size)
        self.open_osm2cr_lanelets.clicked.connect(self.osm_cr_lanelets_menu)

    def opendrive_conversion_menu(self):
        """Open the conversion tool for OpenDRIVE in a new window."""

        viewer = QMainWindow(self)
        opendrive_convert_window = OpenDriveConvertWindow(argv=[], parent=self)
        viewer.setCentralWidget(opendrive_convert_window)
        viewer.show()
        opendrive_convert_window.openOpenDriveFileDialog()

    def commonroad_visualization_menu(self):
        """Open the simple color-supported visualization of a CommonRoad file."""
        viewer = QMainWindow(self)
        commonroad_viewer_widget = ViewerWidget(self)
        viewer.setCentralWidget(commonroad_viewer_widget)
        viewer.show()
        commonroad_viewer_widget.openCommonRoadFile()

    def osm_cr_lanelets_menu(self):
        """Open the menu for the lanelet conversion between OSM and CR"""
        viewer = QMainWindow(self)
        osmcr_lanelets_window = OSMLaneletsConvertWindow(parent=self)
        viewer.setCentralWidget(osmcr_lanelets_window)
        viewer.show()


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
        path, _ = QFileDialog.getSaveFileName(
            self,
            "QFileDialog.getSaveFileName()",
            "",
            "CommonRoad files (*.xml)",
            options=QFileDialog.Options(),
        )

        if not path:
            return

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
            with open(f"{path}", "w") as file_out:
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


class OpenDriveConvertWindow(QWidget):
    """ """

    def __init__(self, argv, parent=None):
        super().__init__(parent=parent)

        self.loadedRoadNetwork = None

        self._init_user_interface()
        self.show()

        if len(argv) >= 2:
            self.load_opendriveFile(argv[1])
            self.viewConvertedLaneletNetwork()

    def _init_user_interface(self):
        """ """

        self.setWindowTitle("OpenDRIVE 2 Lanelets Converter")

        self.setFixedSize(560, 345)

        self.load_button = QPushButton("Load OpenDRIVE", self)
        self.load_button.setToolTip("Load a OpenDRIVE scenario within a *.xodr file")
        self.load_button.move(10, 10)
        self.load_button.resize(130, 35)
        self.load_button.clicked.connect(self.openOpenDriveFileDialog)

        self.inputOpenDriveFile = QLineEdit(self)
        self.inputOpenDriveFile.move(150, 10)
        self.inputOpenDriveFile.resize(400, 35)
        self.inputOpenDriveFile.setReadOnly(True)

        self.statsText = QLabel(self)
        self.statsText.move(10, 55)
        self.statsText.resize(540, 235)
        self.statsText.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.statsText.setTextFormat(Qt.RichText)

        self.exportCommonRoadButton = QPushButton("Export as CommonRoad", self)
        self.exportCommonRoadButton.move(10, 300)
        self.exportCommonRoadButton.resize(170, 35)
        self.exportCommonRoadButton.setDisabled(True)
        self.exportCommonRoadButton.clicked.connect(self.exportAsCommonRoad)

        self.viewOutputButton = QPushButton("View Road Network", self)
        self.viewOutputButton.move(190, 300)
        self.viewOutputButton.resize(170, 35)
        self.viewOutputButton.setDisabled(True)
        self.viewOutputButton.clicked.connect(self.viewConvertedLaneletNetwork)

    def reset_output_elements(self):
        """ """
        self.exportCommonRoadButton.setDisabled(True)
        self.viewOutputButton.setDisabled(True)

    def openOpenDriveFileDialog(self):
        """ """
        print(15)
        self.reset_output_elements()

        path, _ = QFileDialog.getOpenFileName(
            self,
            "QFileDialog.getOpenFileName()",
            "",
            "OpenDRIVE files *.xodr (*.xodr)",
            options=QFileDialog.Options(),
        )

        if not path:
            return

        self.load_opendriveFile(path)

    def load_opendriveFile(self, path):
        """

        Args:
          path:

        Returns:

        """

        filename = os.path.basename(path)
        self.inputOpenDriveFile.setText(filename)

        # Load road network and print some statistics
        try:
            fh = open(path, "r")
            openDriveXml = parse_opendrive(etree.parse(fh).getroot())
            fh.close()
        except (etree.XMLSyntaxError) as e:
            errorMsg = "XML Syntax Error: {}".format(e)
            QMessageBox.warning(
                self,
                "OpenDRIVE error",
                "There was an error during the loading of the selected OpenDRIVE file.\n\n{}".format(
                    errorMsg
                ),
                QMessageBox.Ok,
            )
            return
        except (TypeError, AttributeError, ValueError) as e:
            errorMsg = "Value Error: {}".format(e)
            QMessageBox.warning(
                self,
                "OpenDRIVE error",
                "There was an error during the loading of the selected OpenDRIVE file.\n\n{}".format(
                    errorMsg
                ),
                QMessageBox.Ok,
            )
            return

        self.loadedRoadNetwork = Network()
        self.loadedRoadNetwork.load_opendrive(openDriveXml)

        self.statsText.setText(
            """Name: {}<br>Version: {}<br>Date: {}<br><br>OpenDRIVE
            Version {}.{}<br><br>Number of roads: {}<br>Total length
            of road network: {:.2f} meters""".format(
                openDriveXml.header.name
                if openDriveXml.header.name
                else "<i>unset</i>",
                openDriveXml.header.version,
                openDriveXml.header.date,
                openDriveXml.header.revMajor,
                openDriveXml.header.revMinor,
                len(openDriveXml.roads),
                sum([road.length for road in openDriveXml.roads]),
            )
        )

        self.exportCommonRoadButton.setDisabled(False)
        self.viewOutputButton.setDisabled(False)

    def exportAsCommonRoad(self):
        """ """

        if not self.loadedRoadNetwork:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "QFileDialog.getSaveFileName()",
            "",
            "CommonRoad files *.xml (*.xml)",
            options=QFileDialog.Options(),
        )

        if not path:
            return

        try:
            with open(path, "w") as fh:
                writer = CommonRoadFileWriter(
                    scenario=self.loadedRoadNetwork.export_commonroad_scenario(),
                    planning_problem_set=None,
                    author="",
                    affiliation="",
                    source="OpenDRIVE 2 Lanelet Converter",
                    tags="",
                )
                writer.write_scenario_to_file_io(fh)
        except (IOError) as e:
            QMessageBox.critical(
                self,
                "CommonRoad file not created!",
                "The CommonRoad file was not exported due to an error.\n\n{}".format(e),
                QMessageBox.Ok,
            )
            return

        QMessageBox.information(
            self,
            "CommonRoad file created!",
            "The CommonRoad file was successfully exported.",
            QMessageBox.Ok,
        )

    def viewConvertedLaneletNetwork(self):
        """ """

        class ViewerWindow(QMainWindow):
            """ """

            def __init__(self, parent=None):
                super(ViewerWindow, self).__init__(parent)
                self.viewer = ViewerWidget(self)

                self.setCentralWidget(self.viewer)

        viewer = ViewerWindow(self)
        viewer.viewer.openScenario(self.loadedRoadNetwork.export_commonroad_scenario())
        viewer.show()


if __name__ == "__main__":
    main()
