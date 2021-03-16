import pickle

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from commonroad.scenario.traffic_sign import *

from crmapconverter.io.scenario_designer.toolboxes.map_converter_toolbox_ui import MapConversionToolboxUI
from crmapconverter.io.scenario_designer.osm_gui_modules.gui_embedding import EdgeEdit, LaneLinkEdit
from crmapconverter.io.scenario_designer.osm_gui_modules import gui

from crmapconverter.osm2cr.converter_modules import converter
from crmapconverter.osm2cr.converter_modules.graph_operations import road_graph as rg
from crmapconverter.osm2cr.converter_modules.osm_operations.downloader import download_around_map


class MapConversionToolbox(QDockWidget):
    def __init__(self):
        super().__init__("Map Converter Toolbox")

        self.converter_toolbox = MapConversionToolboxUI()
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
        # window.b_download.clicked.connect(self.download_map)
        # window.coordinate_input.textChanged.connect(self.verify_coordinate_input)
        # window.rb_load_file.clicked.connect(self.load_file_clicked)
        # window.input_bench_id.textChanged.connect(self.bench_id_set)
        # window.rb_download_map.clicked.connect(self.download_map_clicked)

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
        self.app.export(graph)

    def start_conversion(self) -> None:
        """
        Starts the OSM conversion process by picking a file and showing the edge edit GUI.

        :return: None
        """
        try:
            if self.embedding.rb_load_file.isChecked():
                if self.selected_file is not None:
                    self.read_osm_file(self.selected_file)
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
        if self.embedding.chk_user_edit.isChecked():
            self.app.edge_edit_embedding(self.graph)
        else:
            self.hidden_conversion(self.graph)

    def verify_coordinate_input(self) -> bool:
        """
        check if user input of coordinates are in correct format and sane

        :return: True if coordinates are valid
        """
        coords = self.embedding.coordinate_input.text()
        try:
            lat, lon = coords.split(", ")
            self.lat, self.lon = float(lat), float(lon)
            if not (-90 <= self.lat <= 90 and -180 <= self.lon <= 180):
                raise ValueError
            self.embedding.l_region.setText("Coordinates Valid")
            if self.embedding.rb_download_map.isChecked():
                self.embedding.input_picked_output.setText("Map will be downloaded")
            return True
        except ValueError:
            self.embedding.l_region.setText("Coordinates Invalid")
            if self.embedding.rb_download_map.isChecked():
                self.embedding.input_picked_output.setText(
                    "Cannot download, invalid Coordinates"
                )
            return False

    def download_map(self) -> Optional[str]:
        """
        downloads map, but does not open it

        :return: the file name
        """
        name = config.BENCHMARK_ID + ".osm"
        if not self.verify_coordinate_input():
            QMessageBox.critical(
                self,
                "Warning",
                "cannot download, coordinates invalid",
                QMessageBox.Ok)
            return None
        else:
            download_around_map(
                name, self.lat, self.lon, self.embedding.range_input.value()
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