from lxml import etree
from typing import Callable, Optional
import logging
from pathlib import Path

from crdesigner.map_conversion.lanelet2.cr2lanelet import CR2LaneletConverter
from crdesigner.map_conversion.lanelet2.lanelet2_parser import Lanelet2Parser
from crdesigner.map_conversion.lanelet2.lanelet2cr import Lanelet2CRConverter
from crdesigner.map_conversion.map_conversion_interface import osm_to_commonroad_using_sumo
from crdesigner.map_conversion.opendrive.opendrive_parser.parser import parse_opendrive
from crdesigner.map_conversion.osm2cr.converter_modules.cr_operations.export import convert_to_scenario
from crdesigner.map_conversion.osm2cr.converter_modules.osm_operations.downloader import download_around_map
from crdesigner.ui.gui.model.scenario_model import ScenarioModel
from crdesigner.ui.gui.utilities.converter_modules.osm_interface import OSMInterface
from crdesigner.ui.gui.utilities.gui_sumo_simulation import SUMO_AVAILABLE
from crdesigner.ui.gui.utilities.util import select_local_file
from crdesigner.config.osm_config import osm_config
from crdesigner.ui.gui.utilities.waitingspinnerwidget import QtWaitingSpinner
from crdesigner.ui.gui.view.toolboxes.converter_toolbox.converter_toolbox_ui import \
    MapConversionToolboxUI
from PyQt5.QtCore import Qt, QRunnable, QThreadPool, QMetaObject, Q_ARG, pyqtSlot
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations import road_graph as rg
from PyQt5.QtWidgets import QDockWidget, QMainWindow, QFileDialog, QMessageBox
from crdesigner.map_conversion.osm2cr.converter_modules import converter
from crdesigner.map_conversion.opendrive.opendrive_conversion.network import Network
if SUMO_AVAILABLE:
    from crdesigner.ui.gui.utilities.gui_sumo_simulation import SUMOSimulation
    from crdesigner.ui.gui.utilities.converter_modules.sumo_settings import SUMOSettings
    from crdesigner.map_conversion.sumo_map.sumo2cr import convert_net_to_cr


class RequestRunnable(QRunnable):
    def __init__(self, fun, map_conversion_toolbox_controller):
        QRunnable.__init__(self)
        self.fun = fun
        self.mapConversionToolboxController = map_conversion_toolbox_controller

    def run(self):
        self.fun()
        QMetaObject.invokeMethod(self.mapConversionToolboxController, "stop_spinner", Qt.QueuedConnection,
                                 Q_ARG(str, "Conversion Ended"))


def start_spinner(spinner: QtWaitingSpinner):
    if spinner.is_spinning():
        spinner.stop()
    spinner.start()


class MapConversionToolboxController(QDockWidget):
    def __init__(self,  mwindow):
        super().__init__("Map Converter Toolbox")
        self.converter_toolbox_ui = MapConversionToolboxUI(mwindow)
        self.scenario_model = mwindow.scenario_model
        self.mwindow = mwindow
        self.text_browser = mwindow.crdesigner_console_wrapper.text_browser
        self.adjust_ui()
        self.osm_edit_window = QMainWindow(self)
        self.connect_gui_elements()

        if SUMO_AVAILABLE:
            self.sumo_simulation = SUMOSimulation(tmp_folder=mwindow.tmp_folder)
        else:
            self.sumo_simulation = None

        self.lanelet2_to_cr_converter = Lanelet2CRConverter()
        self.lanelet2_file = None
        self.osm_file = None
        self.path_sumo_file = None
        self.open_drive_file = None
        self.graph = None

    def adjust_ui(self):
        """Updates GUI properties like width, etc."""
        self.setFloating(True)
        self.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.setAllowedAreas(Qt.RightDockWidgetArea)
        self.setWidget(self.converter_toolbox_ui)
        self.converter_toolbox_ui.setMinimumWidth(450)

    def adjust_sections(self):
        """
        Adjust sections depending on the selection of the radio buttons.
        Connects buttons with corresponding functions.
        """

        self.converter_toolbox_ui.adjust_sections()

        if self.converter_toolbox_ui.open_drive.isChecked():
            self.converter_toolbox_ui.button_convert_opendrive.clicked.connect(lambda: self.load_open_drive())
        elif self.converter_toolbox_ui.lanelet.isChecked():
            self.converter_toolbox_ui.button_convert_lanelet2_to_cr.clicked.connect(lambda: self.load_lanelet2())
            self.converter_toolbox_ui.button_convert_cr_to_lanelet2.clicked.connect(lambda:
                                                                                    self.convert_cr_to_lanelet2())
        elif self.converter_toolbox_ui.osm.isChecked():
            self.converter_toolbox_ui.button_start_osm_conversion.clicked.connect(
                    lambda: self.convert_osm_with_spinner(self.convert_osm_to_cr))
            self.converter_toolbox_ui.button_start_osm_conversion_with_sumo_parser.clicked.connect(
                    lambda: self.convert_osm_with_spinner(self.convert_osm_to_cr_with_sumo))
        elif self.converter_toolbox_ui.sumo.isChecked():
            self.converter_toolbox_ui.button_convert_sumo_to_cr.clicked.connect(lambda: self.load_sumo())
            self.converter_toolbox_ui.button_convert_cr_to_sumo.clicked.connect(lambda: self.convert_cr_to_sumo())

    def connect_gui_elements(self):
        """
        Connects radiobuttons with function to adjust sections.
        Relevant fields gets shown and unnecessary fields gets hidden on click.
        """
        self.converter_toolbox_ui.open_drive.clicked.connect(lambda: self.adjust_sections())
        self.converter_toolbox_ui.lanelet.clicked.connect(lambda: self.adjust_sections())
        self.converter_toolbox_ui.osm.clicked.connect(lambda: self.adjust_sections())
        self.converter_toolbox_ui.sumo.clicked.connect(lambda: self.adjust_sections())

    def refresh_toolbox(self, model: ScenarioModel):
        self.scenario_model = model

    def load_osm_file(self) -> None:
        """
        Allows to select an OSM file from the file system and loads it.
        """
        filename = select_local_file(self, "OSM", "osm")
        if filename != "":
            self.osm_file = filename

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
        converted_to_scenario = convert_to_scenario(graph)
        self.scenario_model.add_converted_scenario(converted_to_scenario)

    def convert_osm_with_spinner(self, convert_function: Callable[[], None]) -> None:
        """
        Calls function in new thread ands shows spinner.
        :param convert_function: Function which should be called
        """
        if self.mwindow.play_activated:
            self.text_browser.append("Please stop the animation first.")
            return

        start_spinner(self.converter_toolbox_ui.Spinner)
        runnable = RequestRunnable(convert_function, self)
        QThreadPool.globalInstance().start(runnable)

    def convert_osm_to_cr(self) -> None:
        """
        Starts the OSM conversion process by picking a file or downloading a map and showing the edge edit GUI.
        """
        if self.mwindow.play_activated:
            self.text_browser.append("Please stop the animation first.")
            return

        if self.converter_toolbox_ui.load_local_file.isChecked():
            self.load_osm_file()
        else:
            self.download_osm_map()

        try:
            if self.osm_file is not None:
                e = self.read_osm_file(self.osm_file)
                if e is not None:
                    print("__Warning__: {}.".format(e))
                    return
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

        self.hidden_osm_conversion(self.graph)
        self.osm_file = None

    def convert_osm_to_cr_with_sumo(self) -> None:
        """
        Starts the OSM conversion process using SUMO Parser by picking a file and showing the edge edit GUI.
        """
        if self.converter_toolbox_ui.load_local_file.isChecked():
            self.load_osm_file()
        else:
            self.download_osm_map()

        try:
            if self.osm_file is not None:
                osm_to_commonroad_using_sumo_ = osm_to_commonroad_using_sumo(self.osm_file)
                self.scenario_model.add_converted_scenario(osm_to_commonroad_using_sumo_)

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
        self.osm_file = None

    @pyqtSlot(str)
    def stop_spinner(self, data):
        self.scenario_model.notify_all()
        self.converter_toolbox_ui.Spinner.stop()

    def verify_osm_coordinate_input(self) -> bool:
        """
        check if user input of coordinates are in correct format and sane

        :return: True if coordinates are valid
        """
        lat = self.converter_toolbox_ui.osm_conversion_coordinate_latitude.text()
        lon = self.converter_toolbox_ui.osm_conversion_coordinate_longitude.text()
        try:
            lat = float(lat)
            lon = float(lon)
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError
            return True
        except ValueError:
            self.converter_toolbox_ui.osm_loading_status.setText("Cannot download, invalid Coordinates")
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
                name, float(self.converter_toolbox_ui.osm_conversion_coordinate_latitude.text()),
                float(self.converter_toolbox_ui.osm_conversion_coordinate_longitude.text()),
                self.converter_toolbox_ui.osm_download_map_range.value()
            )
            self.osm_file = osm_config.SAVE_PATH + name

    def read_osm_file(self, file: str) -> Optional[Exception]:
        """
        loads an osm file and performs first steps to create the road graph

        :param file: file name
        :return: None or Exception
        """
        try:
            self.graph = converter.step_collection_1(file)
        except Exception as e:
            return e

    def open_osm_settings(self):
        osm_interface = OSMInterface(self)
        osm_interface.show_settings()

    def convert_open_drive_to_cr_with_spinner(self) -> None:
        """
        Starts the OpenDRIVE conversion process by picking a file and converting it while showing a spinner.
        """
        if self.open_drive_file is not None:
            start_spinner(self.converter_toolbox_ui.Spinner)
            runnable = RequestRunnable(self.convert_open_drive_to_cr, self)
            QThreadPool.globalInstance().start(runnable)
        else:
            QMessageBox.warning(self, "Warning", "No file selected.", QMessageBox.Ok)
            return

    def convert_open_drive_to_cr(self):
        """
        Starts the OpenDRIVE conversion process by picking a file and converting it without showing a spinner.
        """
        if self.open_drive_file is None:
            return

        open_drive_network = Network()
        open_drive_network.load_opendrive(self.open_drive_file)

        self.text_browser.append("""Name: {}<br>Version: {}<br>Date: {}<br><br>OpenDRIVE
                Version {}.{}""".format(
                self.open_drive_file.header.name if self.open_drive_file.header.name else "<i>unset</i>",
                self.open_drive_file.header.version, self.open_drive_file.header.date,
                self.open_drive_file.header.revMajor, self.open_drive_file.header.revMinor,
                len(self.open_drive_file.roads), ))
        self.open_drive_file = None
        exported_commonroad_scenario = open_drive_network.export_commonroad_scenario()
        self.scenario_model.add_converted_scenario(exported_commonroad_scenario)

    def load_open_drive(self):
        """
        Allows to select an OpenDRIVE file from the file system and loads it and afterwards calls conversion.
        """
        if self.mwindow.play_activated:
            self.text_browser.append("Please stop the animation first.")
            return

        file_path = select_local_file(self, "OpenDRIVE", "xodr")
        if not file_path:
            return

        # Load road network and print some statistics
        try:
            self.open_drive_file = parse_opendrive(Path(file_path))
        except etree.XMLSyntaxError as e:
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

        self.convert_open_drive_to_cr_with_spinner()

    def load_lanelet2(self):
        """
        Allows to select a lanelet file from the file system and loads it and calls conversion.
        """
        if self.mwindow.play_activated:
            self.text_browser.append("Please stop the animation first.")
            return

        file_path = select_local_file(self, "Lanelet/Lanelet2", "osm")
        if not file_path:
            return

        # Load road network and print some statistics
        try:
            with open(file_path, "r") as fd:
                parser = Lanelet2Parser(etree.parse(fd).getroot())
                self.lanelet2_file = parser.parse()
        except etree.XMLSyntaxError as e:
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

        self.convert_lanelet2_to_cr()

    def convert_lanelet2_to_cr(self):
        """
        Starts the Lanelet to CommonRoad conversion process.
        """
        try:
            if self.lanelet2_file is None:
                QMessageBox.warning(None, "Warning", "No file selected.", QMessageBox.Ok)
                return
            scenario = self.lanelet2_to_cr_converter(self.lanelet2_file)
            self.lanelet2_file = None
            self.scenario_model.add_converted_scenario(scenario)
            self.text_browser.append("Conversion from Lanelet2 to CommonRoad is done")
        except Exception as e:
            logging.error(f"MapConversionToolboxController::convert_lanelet2_to_cr: {e}")

    def convert_cr_to_lanelet2(self):
        """
        Starts the CommonRoad to Lanelet conversion process.
        """
        if self.mwindow.play_activated:
            self.text_browser.append("Please stop the animation first.")
            return

        directory = QFileDialog.getExistingDirectory(self, "Dir", options=QFileDialog.Options())

        if not self.scenario_model.scenario_created or directory == "":
            return
        path = directory + "/" + str(self.scenario_model.get_scenario_id()) + ".osm"
        l2osm = CR2LaneletConverter()
        osm = l2osm(self.scenario_model.get_current_scenario())
        with open(f"{path}", "wb") as file_out:
            file_out.write(
                etree.tostring(
                    osm, xml_declaration=True, encoding="UTF-8", pretty_print=True
                )
            )
        self.text_browser.append("Conversion from CommonRoad to Lanelet2 is done")

    def load_sumo(self):
        """
        Allows to select a SUMO file from the file system and loads it and calls conversion.
        """
        if self.mwindow.play_activated:
            self.text_browser.append("Please stop the animation first.")
            return

        if SUMO_AVAILABLE:
            self.path_sumo_file = select_local_file(self, "SUMO", "net.xml")

            if not self.path_sumo_file:
                return

            self.convert_sumo_to_cr()
        else:
            logging.warning("Cannot import SUMO. SUMO simulation will not be offered in Scenario Designer GUI. "
                            "The GUI and other map conversions should work.")

    def convert_cr_to_sumo(self):
        """
        Starts the CommonRoad to SUMO conversion process.
        """
        if self.mwindow.play_activated:
            self.text_browser.append("Please stop the animation first.")
            return

        if SUMO_AVAILABLE:
            directory = QFileDialog.getExistingDirectory(self, "Dir", options=QFileDialog.Options())
            if not directory:
                return
            self.sumo_simulation.convert(directory)
        else:
            logging.warning("Cannot import SUMO. SUMO simulation will not be offered in Scenario Designer GUI. "
                            "The GUI and other map conversions should work.")

    def open_sumo_settings(self):
        if SUMO_AVAILABLE:
            SUMOSettings(self, config=self.sumo_simulation.config)
        else:
            logging.warning("Cannot import SUMO. SUMO simulation will not be offered in Scenario Designer GUI. "
                            "The GUI and other map conversions should work.")

    def convert_sumo_to_cr(self):
        """
        Starts the SUMO to CommonRoad conversion process.
        """
        if SUMO_AVAILABLE:
            try:
                scenario = convert_net_to_cr(self.path_sumo_file)
                self.scenario_model.set_scenario(scenario)
            except Exception as e:
                QMessageBox.warning(self, "Internal Error",
                                    "There was an error during the processing of the graph.\n\n{}".format(e),
                                    QMessageBox.Ok)
                return
        else:
            logging.warning("Cannot import SUMO. SUMO simulation will not be offered in Scenario Designer GUI. "
                            "The GUI and other map conversions should work.")
