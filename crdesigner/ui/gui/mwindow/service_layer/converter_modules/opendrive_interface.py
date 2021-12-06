import os
from lxml import etree


from PyQt5.QtWidgets import QFileDialog, QMessageBox

from crdesigner.map_conversion.opendrive.opendrive_parser.parser import parse_opendrive
from crdesigner.map_conversion.opendrive.opendrive_conversion.network import Network
from crdesigner.ui.gui.mwindow.service_layer.converter_modules.converter_interface import ConverterInterface


class OpenDRIVEInterface(ConverterInterface):

    def __init__(self, parent):
        self.cr_designer = parent
        self.loadedRoadNetwork = None
        self.stats_Text = None
        self.filename = None

    def start_import(self):
        """  """
        file_path, _ = QFileDialog.getOpenFileName(
            self.cr_designer,
            "select OpenDRIVE file to convert",
            "",
            "OpenDRIVE files *.xodr (*.xodr)",
            options=QFileDialog.Options(),
        )

        if not file_path:
            # self.NoFileselected()
            return

        # Load road network and print some statistics
        try:
            with open(file_path, "r") as fd:
                openDriveXml = parse_opendrive(etree.parse(fd).getroot())
        except (etree.XMLSyntaxError) as e:
            errorMsg = "XML Syntax Error: {}".format(e)
            QMessageBox.warning(
                self.cr_designer,
                "OpenDRIVE error",
                "There was an error during the loading of the selected OpenDRIVE file.\n\n{}"
                    .format(errorMsg),
                QMessageBox.Ok,
            )
            return
        except (TypeError, AttributeError, ValueError) as e:
            errorMsg = "Value Error: {}".format(e)
            QMessageBox.warning(
                self.cr_designer,
                "OpenDRIVE error",
                "There was an error during the loading of the selected OpenDRIVE file.\n\n{}"
                    .format(errorMsg),
                QMessageBox.Ok,
            )
            return

        self.loadedRoadNetwork = Network()
        self.loadedRoadNetwork.load_opendrive(openDriveXml)

        self.cr_designer.text_browser.append(
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

        scenario = self.loadedRoadNetwork.export_commonroad_scenario()
        self.filename = os.path.basename(file_path)
        self.filename = os.path.splitext(self.filename)[0]
        self.cr_designer.open_scenario(scenario, self.filename)

    # def NoFileselected(self):
    #     mbox = QMessageBox()
    #     reply = mbox.information(
    #         None,
    #         "Information",
    #         "Please select a OpenDrive file",
    #         QMessageBox.Ok | QMessageBox.No,
    #         QMessageBox.Ok)
    #     if reply == QMessageBox.Ok:
    #         self.open_opendrive_file_dialog()
    #     else:
    #         mbox.close()