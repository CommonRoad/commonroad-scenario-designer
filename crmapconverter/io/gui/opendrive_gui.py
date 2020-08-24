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

from crmapconverter.opendrive.opendriveparser.parser import parse_opendrive
from crmapconverter.opendrive.opendriveconversion.network import Network
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


class OpenDriveConvertWindow(QWidget):
    """
    GUI of the the tool to convert map from Open Drive to Common Road
    """

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
        self.reset_output_elements()

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select an Open Drive Map",
            "",
            "OpenDRIVE files *.xodr (*.xodr)",
            options=QFileDialog.Options(),
        )

        if not path:
            return

        self.load_opendriveFile(path)

        return path

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

        # Hidden for the Tkinter conversion
        """QMessageBox.information(
            self,
            "CommonRoad file created!",
            "The CommonRoad file was successfully exported.",
            QMessageBox.Ok,
        )"""

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
