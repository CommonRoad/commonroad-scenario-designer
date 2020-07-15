import os
from lxml import etree

from crmapconverter.opendriveparser.parser import parse_opendrive
from crmapconverter.opendriveconversion.network import Network
from crmapconverter.io.V3_0.gui_cr_viewer import CrViewer

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class OD2CR:
    """
        realize OD2CR converter module
        """

    def __init__(self, parent):
        self.cr_designer = parent
        self.statsText = None
        self.filename = None
        self.current_scenario = None

        self.open_opendrive_file_dialog()

    def open_opendrive_file_dialog(self):
        """ """
        # self.reset_output_elements()

        path, _ = QFileDialog.getOpenFileName(
            None,
            "QFileDialog.getOpenFileName()",
            "",
            "OpenDRIVE files *.xodr (*.xodr)",
            options=QFileDialog.Options(),
        )

        if not path:
            self.NoFileselected()
            self.cr_designer.textBrowser.append(
                "Terminated because no OpenDrive file selected")
            return

        self.load_opendrive_file(path)

    def load_opendrive_file(self, path):
        """

        Args:
          path:

        Returns:

        """

        filename = os.path.basename(path)
        self.filename = filename

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

        self.statsText = (
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

        self.open_scenario()

    def open_scenario(self):
        """

        Args:
          scenario:

        Returns:

        """
        self.current_scenario = self.loadedRoadNetwork.export_commonroad_scenario()
        self.cr_designer.open_scenario(self.current_scenario, self.filename)

    def NoFileselected(self):
        mbox = QMessageBox()
        reply = mbox.information(
            None,
            "Information",
            "Please select a OpenDrive file",
            QMessageBox.Ok | QMessageBox.No,
            QMessageBox.Ok)
        if reply == QMessageBox.Ok:
            self.open_opendrive_file_dialog()
        else:
            mbox.close()


