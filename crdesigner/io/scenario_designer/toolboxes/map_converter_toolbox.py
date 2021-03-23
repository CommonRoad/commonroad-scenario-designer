import pickle
from lxml import etree

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from commonroad.scenario.traffic_sign import *

from crdesigner.io.scenario_designer.toolboxes.map_converter_toolbox_ui import MapConversionToolboxUI
from crdesigner.io.scenario_designer.osm_gui_modules.gui_embedding import EdgeEdit, LaneLinkEdit
from crdesigner.io.scenario_designer.osm_gui_modules import gui

from crdesigner.osm2cr.converter_modules import converter
from crdesigner.osm2cr.converter_modules.cr_operations.export import convert_to_scenario
from crdesigner.osm2cr.converter_modules.graph_operations import road_graph as rg
from crdesigner.osm2cr.converter_modules.osm_operations.downloader import download_around_map

from crdesigner.opendrive.opendriveparser.parser import parse_opendrive
from crdesigner.opendrive.opendriveconversion.network import Network

from crdesigner.lanelet_lanelet2.parser import OSMParser
from crdesigner.lanelet_lanelet2.osm2lanelet import OSM2LConverter


class MapConversionToolbox(QDockWidget):
    def __init__(self, callback, text_browser):
        super().__init__("Map Converter Toolbox")

        self.converter_toolbox = MapConversionToolboxUI()
        self.callback = callback
        self.text_browser = text_browser
        self.selected_osm_file = None
        self.adjust_ui()
        self.connect_gui_elements()

    def adjust_ui(self):
        """Updates GUI properties like width, etc."""
        self.setFloating(True)
        self.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.setAllowedAreas(Qt.RightDockWidgetArea)
        self.setWidget(self.converter_toolbox)

    def connect_gui_elements(self):
        self.converter_toolbox.button_start_osm_conversion.clicked.connect(lambda: self.start_conversion())
        self.converter_toolbox.button_select_osm_file.clicked.connect(lambda: self.select_file())
        self.converter_toolbox.button_load_osm_edit_state.clicked.connect(lambda: self.load_edit_state())
        self.converter_toolbox.button_load_open_drive.clicked.connect(lambda: self.convert_open_drive())
        self.converter_toolbox.button_load_lanelet2.clicked.connect(lambda: self.convert_lanelet())

    def load_edit_state(self) -> None:
        """
        Loads an OSM edit state and opens it within a separate GUI.
        """
        filename, _ = QFileDialog.getOpenFileName(self, "Select a edit state file", "", "edit save *.save (*.save)",
                                                  options=QFileDialog.Options())
        if filename == "" or filename is None:
            print("no file picked")
        else:
            with open(filename, "rb") as fd:
                gui_state = pickle.load(fd)
            if isinstance(gui_state, gui.EdgeEditGUI):
                EdgeEdit(self.app, None, gui_state)
                self.app.main_window.show()
            elif isinstance(gui_state, gui.LaneLinkGUI):
                LaneLinkEdit(self.app, None, gui_state)
                self.app.main_window.show()
            else:
                QMessageBox.critical(self, "Warning", "Invalid GUI state.", QMessageBox.Ok)
                return

    def select_file(self) -> None:
        """
        Allows to select an OSM file from the file system and loads it.
        """

        filename, _ = QFileDialog.getOpenFileName(self, "Select OpenStreetMap File", "",
                                                  "OpenStreetMap file *.osm (*.osm)", options=QFileDialog.Options())
        if filename != "":
            self.selected_osm_file = filename

    def hidden_conversion(self, graph: rg.Graph) -> None:
        """
        Performs a OSM conversion without user edit.

        :param graph: graph to convert
        """
        try:
            graph = converter.step_collection_2(graph)
            graph = converter.step_collection_3(graph)
        except Exception as e:
            QMessageBox.warning(self, "Internal Error", "There was an error during the processing of the graph.\n\n{}"
                                .format(e), QMessageBox.Ok)
            return
        scenario = convert_to_scenario(graph)
        self.callback(scenario)

    def start_conversion(self) -> None:
        """
        Starts the OSM conversion process by picking a file and showing the edge edit GUI.

        :return: None
        """
        try:
            if self.converter_toolbox.osm_conversion_load_osm_file_selection.isChecked():
                if self.selected_osm_file is not None:
                    self.read_osm_file(self.selected_osm_file)
                else:
                    QMessageBox.warning(
                        self,
                        "Warning",
                        "No file selected.",
                        QMessageBox.Ok)
                    return
            else:
                self.download_and_open_osm_file()
        except ValueError as e:
            QMessageBox.critical(
                self,
                "Warning",
                "Map unreadable: " + str(e),
                QMessageBox.Ok)
            return
        if self.converter_toolbox.osm_conversion_edit_manually_selection.isChecked():
            self.app.edge_edit_embedding(self.graph)
        else:
            self.hidden_conversion(self.graph)

    def verify_coordinate_input(self) -> bool:
        """
        check if user input of coordinates are in correct format and sane

        :return: True if coordinates are valid
        """
        lat = self.converter_toolbox.osm_conversion_coordinate_latitude.text()
        lon = self.converter_toolbox.osm_conversion_coordinate_longitude.text()
        try:
            lat = float(lat)
            lon = float(lon)
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError
            #self.embedding.l_region.setText("Coordinates Valid")
         #   if self.converter_toolbox.osm_conversion_download_osm_file_selection.isChecked():
         #       self.embedding.input_picked_output.setText("Map will be downloaded")
            return True
        except ValueError:
            # self.embedding.l_region.setText("Coordinates Invalid")
            # if self.embedding.rb_download_map.isChecked():
            #     self.embedding.input_picked_output.setText(
            #         "Cannot download, invalid Coordinates"
            #     )
            return False

    def download_map(self) -> Optional[str]:
        """
        downloads map, but does not open it

        :return: the file name
        """
        name = "test" + ".osm"
        if not self.verify_coordinate_input():
            QMessageBox.critical(
                self,
                "Warning",
                "cannot download, coordinates invalid",
                QMessageBox.Ok)
            return None
        else:
            download_around_map(
                name, self.lat, self.lon, self.converter_toolbox.osm_download_map_range.value()
            )
            return name

    def download_and_open_osm_file(self) -> None:
        """
        downloads the specified region and reads the osm file

        :return: None
        """
        name = self.download_map()
        if name is not None:
            self.read_osm_file(config.SAVE_PATH + name)

    def read_osm_file(self, file: str) -> None:
        """
        loads an osm file and performs first steps to create the road graph

        :param file: file name
        :return: None
        """
        try:
            self.graph = converter.step_collection_1(file)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Internal Error",
                "There was an error during the loading of the selected osm file.\n\n{}"
                .format(e),
                QMessageBox.Ok,
            )

    def convert_open_drive(self):
        """  """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
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
                self,
                "OpenDRIVE error",
                "There was an error during the loading of the selected OpenDRIVE file.\n\n{}"
                    .format(errorMsg),
                QMessageBox.Ok,
            )
            return
        except (TypeError, AttributeError, ValueError) as e:
            errorMsg = "Value Error: {}".format(e)
            QMessageBox.warning(
                self,
                "OpenDRIVE error",
                "There was an error during the loading of the selected OpenDRIVE file.\n\n{}"
                    .format(errorMsg),
                QMessageBox.Ok,
            )
            return

        self.loadedRoadNetwork = Network()
        self.loadedRoadNetwork.load_opendrive(openDriveXml)

        self.text_browser.append(
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
        self.callback(scenario)

    def convert_lanelet(self):
        """  """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "select Lanelet/Lanelet2 file to convert",
            "",
            "Lanelet files *.osm (*.osm)",
            options=QFileDialog.Options(),
        )

        if not file_path:
            return

        # Load road network and print some statistics
        try:
            with open(file_path, "r") as fd:
                parser = OSMParser(etree.parse(fd).getroot())
                osm = parser.parse()
        except (etree.XMLSyntaxError) as e:
            error_message = "XML Syntax Error: {}".format(e)
            QMessageBox.warning(
                self,
                "Lanelet/Lanelet2 error",
                "There was an error during the loading of the selected Lanelet/Lanelet2 file.\n\n{}"
                    .format(error_message),
                QMessageBox.Ok,
            )
            return
        except (TypeError, AttributeError, ValueError) as e:
            error_message = "Value Error: {}".format(e)
            QMessageBox.warning(
                self,
                "Lanelet/Lanelet2 error",
                "There was an error during the loading of the selected Lanelet/Lanelet2 file.\n\n{}"
                    .format(error_message),
                QMessageBox.Ok,
            )
            return

        osm2l = OSM2LConverter()
        scenario = osm2l(osm)
        self.callback(scenario)
