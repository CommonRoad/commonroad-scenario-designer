import pickle
from lxml import etree

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from commonroad.scenario.traffic_sign import *
from commonroad.scenario.scenario import Scenario

from crdesigner.input_output.gui.toolboxes.map_converter_toolbox_ui import MapConversionToolboxUI
from crdesigner.input_output.gui.misc.util import select_local_file

from crdesigner.map_conversion.osm2cr.converter_modules import converter
from crdesigner.map_conversion.osm2cr.converter_modules.osm_operations.downloader import download_around_map
from crdesigner.map_conversion.osm2cr import config
from crdesigner.map_conversion.osm2cr.converter_modules.cr_operations.export import convert_to_scenario
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations import road_graph as rg

from crdesigner.input_output.gui.osm_gui_modules.gui_embedding import EdgeEdit, LaneLinkEdit
from crdesigner.input_output.gui.converter_modules.osm_interface import OSMInterface
from crdesigner.input_output.gui.osm_gui_modules.gui import EdgeEditGUI, LaneLinkGUI

from crdesigner.map_conversion.opendrive.opendrive_parser.parser import parse_opendrive
from crdesigner.map_conversion.opendrive.opendrive_conversion.network import Network

from crdesigner.map_conversion.lanelet_lanelet2.lanelet2_parser import Lanelet2Parser
from crdesigner.map_conversion.lanelet_lanelet2.lanelet2cr import Lanelet2CRConverter
from crdesigner.map_conversion.lanelet_lanelet2.cr2lanelet import CR2LaneletConverter

from crdesigner.input_output.gui.toolboxes.gui_sumo_simulation import SUMO_AVAILABLE
if SUMO_AVAILABLE:
    from crdesigner.input_output.gui.toolboxes.gui_sumo_simulation import SUMOSimulation
    from crdesigner.input_output.gui.settings.sumo_settings import SUMOSettings
    from crdesigner.map_conversion.sumo_map.sumo2cr import convert_net_to_cr


class MapConversionToolbox(QDockWidget):
    def __init__(self, current_scenario, callback, text_browser, tmp_folder: str):
        super().__init__("Map Converter Toolbox")
        self.converter_toolbox = MapConversionToolboxUI()
        self.callback = callback
        self.text_browser = text_browser
        self.adjust_ui()
        self.connect_gui_elements()
        self.osm_edit_window = QMainWindow(self)
        self.current_scenario = current_scenario

        if SUMO_AVAILABLE:
            self.sumo_simulation = SUMOSimulation(tmp_folder=tmp_folder)
        else:
            self.sumo_simulation = None

        self.lanelet2_to_cr_converter = Lanelet2CRConverter()

        self.lanelet2_file = None
        self.osm_file = None
        self.path_sumo_file = None
        self.open_drive_file = None

    def adjust_ui(self):
        """Updates GUI properties like width, etc."""
        self.setFloating(True)
        self.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.setAllowedAreas(Qt.RightDockWidgetArea)
        self.setWidget(self.converter_toolbox)
        self.converter_toolbox.setMinimumWidth(450)

    def connect_gui_elements(self):
        self.converter_toolbox.button_download_osm_file.clicked.connect(lambda: self.download_osm_map())
        self.converter_toolbox.button_load_osm_file.clicked.connect(lambda: self.load_osm_file())
        self.converter_toolbox.button_load_osm_edit_state.clicked.connect(lambda: self.load_osm_edit_state())
        self.converter_toolbox.button_start_osm_conversion.clicked.connect(lambda: self.convert_osm_to_cr())
        self.converter_toolbox.button_open_osm_settings.clicked.connect(lambda: self.open_osm_settings())

        self.converter_toolbox.button_load_opendrive.clicked.connect(lambda: self.load_open_drive())
        self.converter_toolbox.button_convert_opendrive.clicked.connect(lambda: self.convert_open_drive_to_cr())

        self.converter_toolbox.button_load_lanelet2.clicked.connect(lambda: self.load_lanelet2())
        self.converter_toolbox.button_convert_lanelet2_to_cr.clicked.connect(lambda: self.convert_lanelet2_to_cr())
        self.converter_toolbox.button_convert_cr_to_lanelet2.clicked.connect(lambda: self.convert_cr_to_lanelet2())

        self.converter_toolbox.button_load_sumo.clicked.connect(lambda: self.load_sumo())
        self.converter_toolbox.button_convert_sumo_to_cr.clicked.connect(lambda: self.convert_sumo_to_cr())
        self.converter_toolbox.button_convert_cr_to_sumo.clicked.connect(lambda: self.convert_cr_to_sumo())
        self.converter_toolbox.button_open_sumo_settings.clicked.connect(lambda: self.open_sumo_settings())

    def refresh_toolbox(self, scenario: Scenario):
        self.current_scenario = scenario

    def load_osm_edit_state(self) -> None:
        """
        Loads an OSM edit state and opens it within a separate GUI.
        """
        filename, _ = QFileDialog.getOpenFileName(self, "Select a edit state file", "edit save *.save (*.save)",
                                                  options=QFileDialog.Options())
        if filename == "" or filename is None:
            print("no file picked")
        else:
            with open(filename, "rb") as fd:
                gui_state = pickle.load(fd)
            if isinstance(gui_state, EdgeEditGUI):
                EdgeEdit(self, None, gui_state)
                self.osm_edit_window.show()
            elif isinstance(gui_state, LaneLinkGUI):
                LaneLinkEdit(self, None, gui_state)
                self.osm_edit_window.show()
            else:
                QMessageBox.critical(self, "Warning", "Invalid GUI state.", QMessageBox.Ok)
                return

    def load_osm_file(self) -> None:
        """
        Allows to select an OSM file from the file system and loads it.
        """
        filename = select_local_file(self, "OSM", "osm")
        if filename != "":
            self.osm_file = filename
            self.converter_toolbox.osm_loading_status.setText("map successfully loaded")

    def hidden_osm_conversion(self, graph: rg.Graph) -> None:
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

    def convert_osm_to_cr(self) -> None:
        """
        Starts the OSM conversion process by picking a file and showing the edge edit GUI.
        """
        try:
            if self.osm_file is not None:
                self.read_osm_file(self.osm_file)
            else:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "No file selected.",
                    QMessageBox.Ok)
                return
        except ValueError as e:
            QMessageBox.critical(
                self,
                "Warning",
                "Map unreadable: " + str(e),
                QMessageBox.Ok)
            return
        if self.converter_toolbox.osm_conversion_edit_manually_selection.isChecked():
            self.edge_edit_embedding(self.graph)
        else:
            self.hidden_osm_conversion(self.graph)
        self.converter_toolbox.osm_loading_status.setText("no file selected")
        self.osm_file = None

    def edge_edit_embedding(self, graph: rg.Graph):
        """
        sets edge edit embedding as main window

        :param graph: the graph to edit
        :return: None
        """
        if graph is not None:
            self.edge_edit_window = EdgeEdit(self, graph, None)
            self.osm_edit_window.show()
        else:
            print("no graph loaded")

    def lane_link_embedding(self, graph: rg.Graph):
        """
        sets lane link embedding as main window

        :param graph: the graph to edit
        :return:
        """
        if graph is not None:
            self.lane_link_window = LaneLinkEdit(self, graph, None)
            self.osm_edit_window.show()

    def verify_osm_coordinate_input(self) -> bool:
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
            return True
        except ValueError:
            self.converter_toolbox.osm_loading_status.setText("Cannot download, invalid Coordinates")
            return False

    def download_osm_map(self) -> Optional[str]:
        """
        downloads map, but does not open it

        :return: the file name
        """
        name = "openstreetmap_download" + ".osm"
        if not self.verify_osm_coordinate_input():
            QMessageBox.critical(
                self,
                "Warning",
                "cannot download, coordinates invalid",
                QMessageBox.Ok)
            return None
        else:
            download_around_map(
                name, float(self.converter_toolbox.osm_conversion_coordinate_latitude.text()),
                float(self.converter_toolbox.osm_conversion_coordinate_longitude.text()),
                self.converter_toolbox.osm_download_map_range.value()
            )
            self.osm_file = config.SAVE_PATH + name
            self.converter_toolbox.osm_loading_status.setText("map successfully downloaded")

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

    def open_osm_settings(self):
        osm_interface = OSMInterface(self)
        osm_interface.show_settings()

    def convert_open_drive_to_cr(self):
        if self.open_drive_file is None:
            return

        open_drive_network = Network()
        open_drive_network.load_opendrive(self.open_drive_file)

        self.text_browser.append(
            """Name: {}<br>Version: {}<br>Date: {}<br><br>OpenDRIVE
            Version {}.{}<br><br>Number of roads: {}<br>Total length
            of road network: {:.2f} meters""".format(
                self.open_drive_file.header.name if self.open_drive_file.header.name else "<i>unset</i>",
                self.open_drive_file.header.version,
                self.open_drive_file.header.date,
                self.open_drive_file.header.revMajor,
                self.open_drive_file.header.revMinor,
                len(self.open_drive_file.roads),
                sum([road.length for road in self.open_drive_file.roads]),
            )
        )
        self.converter_toolbox.loaded_opendrive_file.setText("no file selected")
        self.open_drive_file = None
        scenario = open_drive_network.export_commonroad_scenario()
        self.callback(scenario)

    def load_open_drive(self):
        file_path = select_local_file(self, "OpenDRIVE", "xodr")
        if not file_path:
            return
        # Load road network and print some statistics
        try:
            with open(file_path, "r") as fd:
                self.open_drive_file = parse_opendrive(etree.parse(fd).getroot())
            self.converter_toolbox.loaded_opendrive_file.setText("file successfully loaded")
        except (etree.XMLSyntaxError) as e:
            error_message = "XML Syntax Error: {}".format(e)
            QMessageBox.warning(
                self,
                "OpenDRIVE error",
                "There was an error during the loading of the selected OpenDRIVE file.\n\n{}".format(error_message),
                QMessageBox.Ok,
            )
            return
        except (TypeError, AttributeError, ValueError) as e:
            error_message = "Value Error: {}".format(e)
            QMessageBox.warning(
                self,
                "OpenDRIVE error",
                "There was an error during the loading of the selected OpenDRIVE file.\n\n{}".format(error_message),
                QMessageBox.Ok,
            )
            return

    def load_lanelet2(self):
        file_path = select_local_file(self, "Lanelet/Lanelet2", "osm")
        if not file_path:
            return

        # Load road network and print some statistics
        try:
            with open(file_path, "r") as fd:
                parser = Lanelet2Parser(etree.parse(fd).getroot())
                self.lanelet2_file = parser.parse()
            self.converter_toolbox.loaded_lanelet_file.setText("file successfully loaded")
        except (etree.XMLSyntaxError) as e:
            error_message = "XML Syntax Error: {}".format(e)
            QMessageBox.warning(
                self,
                "Lanelet/Lanelet2 error",
                "There was an error during the loading of the "
                "selected Lanelet/Lanelet2 file.\n\n{}".format(error_message),
                QMessageBox.Ok,
            )
            return
        except (TypeError, AttributeError, ValueError) as e:
            error_message = "Value Error: {}".format(e)
            QMessageBox.warning(
                self,
                "Lanelet/Lanelet2 error",
                "There was an error during the loading of the selected "
                "Lanelet/Lanelet2 file.\n\n{}".format(error_message),
                QMessageBox.Ok,
            )
            return

    def convert_lanelet2_to_cr(self):
        """  """
        if self.lanelet2_file is not None:
            scenario = self.lanelet2_to_cr_converter(self.lanelet2_file)
            self.lanelet2_file = None
            self.converter_toolbox.loaded_lanelet_file.setText("no file selected")
            self.callback(scenario)

    def convert_cr_to_lanelet2(self):
        directory = QFileDialog.getExistingDirectory(self, "Dir", options=QFileDialog.Options())
        path = directory + "/" + str(self.current_scenario.scenario_id) + ".osm"
        l2osm = CR2LaneletConverter()
        osm = l2osm(self.current_scenario)
        with open(f"{path}", "wb") as file_out:
            file_out.write(
                etree.tostring(
                    osm, xml_declaration=True, encoding="UTF-8", pretty_print=True
                )
            )

    def load_sumo(self):
        self.path_sumo_file = select_local_file(self, "SUMO", "net.xml")
        if self.path_sumo_file:
            self.converter_toolbox.loaded_sumo_file.setText("file successfully loaded")

    def convert_cr_to_sumo(self):
        directory = QFileDialog.getExistingDirectory(self, "Dir", options=QFileDialog.Options())
        if not directory:
            return
        self.sumo_simulation.convert(directory)

    def open_sumo_settings(self):
        SUMOSettings(self, config=self.sumo_simulation.config)

    def convert_sumo_to_cr(self):
        scenario = convert_net_to_cr(self.path_sumo_file)
        self.callback(scenario)

