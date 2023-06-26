import logging
import pathlib

from PyQt5 import QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from crdesigner.ui.gui.controller.animated_viewer.animated_viewer_wrapper_controller import \
    AnimatedViewerWrapperController
from crdesigner.ui.gui.controller.settings.scenario_saving_dialog_controller import ScenarioSavingDialogController
from crdesigner.ui.gui.controller.toolboxes.road_network_controller.road_network_controller import RoadNetworkController
from crdesigner.ui.gui.controller.toolboxes.obstacle_toolbox.obstacle_controller import ObstacleController
from crdesigner.ui.gui.controller.toolboxes.converter_toolbox.map_conversion_controller import MapConversionToolboxController
from crdesigner.ui.gui.controller.top_bar.top_bar_controller import TopBarController
from crdesigner.ui.gui.model.scenario_model import ScenarioModel
from crdesigner.ui.gui.model.settings.gui_settings_model import gui_settings
from crdesigner.ui.gui.view.console.console_ui import ConsoleUI
from crdesigner.ui.gui.utilities.gui_sumo_simulation import SUMO_AVAILABLE
from crdesigner.ui.gui.utilities.util import *
from crdesigner.ui.gui.view.mwindow_ui import MWindowUI


class MWindowController:

    def __init__(self, input_file=None):

        # init or set all attributes here
        self.tmp_folder = gui_settings.MWINDOW_TMP_FOLDER_PATH
        self.filename = None
        self.slider_clicked = False
        self.play_activated = False

        # init scenario model
        self.scenario_model = ScenarioModel()

        # init any objects here
        self.scenario_saving_dialog = ScenarioSavingDialogController()
        # scenario_model is given

        # call the setup methods in the service layer
        self.setup_tmp(tmp_folder_path=self.tmp_folder)

        # init UI
        self.mwindow_ui = MWindowUI()
        self.mwindow_ui.closeEvent = self.close_event

        self.animated_viewer_wrapper = AnimatedViewerWrapperController(mwindow=self.mwindow_ui,
                                                                       scenario_model=self.scenario_model)
        self.mwindow_ui.animated_viewer_wrapper = self.animated_viewer_wrapper
        self.animated_viewer_wrapper.create_viewer_dock()

        # call the setup methods in the service layer
        self.crdesigner_console_wrapper = ConsoleUI(mwindow=self)
        self.mwindow_ui.crdesigner_console_wrapper = self.crdesigner_console_wrapper

        self.road_network_toolbox = RoadNetworkController(mwindow=self)
        self.mwindow_ui.addDockWidget(Qt.LeftDockWidgetArea, self.road_network_toolbox)
        self.mwindow_ui.road_network_toolbox = self.road_network_toolbox

        self.obstacle_toolbox = ObstacleController(mwindow=self)
        self.mwindow_ui.addDockWidget(Qt.RightDockWidgetArea, self.obstacle_toolbox)
        self.mwindow_ui.obstacle_toolbox = self.obstacle_toolbox

        self.map_converter_toolbox = MapConversionToolboxController(mwindow=self)
        self.mwindow_ui.addDockWidget(Qt.RightDockWidgetArea, self.map_converter_toolbox)
        self.mwindow_ui.map_converter_toolbox = self.map_converter_toolbox

        self.mwindow_ui.top_bar = TopBarController(self)

        # IMPORTANT: this has to be after the toolboxes, otherwise the handle used in the fileactions to the viewer_dock
        # gets lost (by the setCentralWidget method)
        self.animated_viewer_wrapper.create_viewer_dock()
        self.status = self.mwindow_ui.statusbar
        self.status.showMessage("Welcome to CR Scenario Designer")

        self.mwindow_ui.update_window()
        self.center()

    def check_scenario(self, scenario) -> int:
        """
        Check the scenario to validity and calculate a quality score.
        The higher the score the higher the data faults.

        Redirect to the service layer.

        :return: score
        """
        return self.check_scenario_service_layer(scenario=scenario)

    def setup_tmp(self, tmp_folder_path: str):
        """
        Set up the tmp folder of the MWindow at the given Path.
        """
        pathlib.Path(tmp_folder_path).mkdir(parents=True, exist_ok=True)

    def center(self):
        """Function that makes sure the main window is in the center of screen."""
        screen = QDesktopWidget().screenGeometry()
        size = self.mwindow_ui.geometry()
        self.mwindow_ui.move(int((screen.width() - size.width()) / 2), int((screen.height() - size.height()) / 2))

    # TODO: MODEL
    def store_scenario_service_layer(self):
        # Moved to scenario_model.py
        #TODO: resolve access to MVC
        scenario = self.mwindow_ui.animated_viewer_wrapper.cr_viewer.current_scenario
        self.scenario_model.store_scenario_service_layer(scenario)

        # TODO: move as signal update  # self.mwindow_ui.update_toolbox_scenarios()

    def update_toolbox_scenarios_service_layer(self):
        #TODO: Update to scenario_model
        scenario = self.mwindow_ui.animated_viewer_wrapper.cr_viewer.current_scenario
        self.mwindow_ui.road_network_toolbox.refresh_toolbox(scenario)
        self.mwindow_ui.obstacle_toolbox.refresh_toolbox(scenario)
        self.mwindow_ui.map_converter_toolbox.refresh_toolbox(scenario)
        if SUMO_AVAILABLE:
            self.mwindow_ui.obstacle_toolbox.sumo_simulation.scenario = scenario
            self.mwindow_ui.map_converter_toolbox.sumo_simulation.scenario = scenario

    def store_scenario(self):
        """ Redirect to the service layer. """
        self.store_scenario_service_layer()

    def check_scenario_service_layer(self, scenario) -> int:
        """
        Check the scenario to validity and calculate a quality score.
        The higher the score the higher the data faults.

        :return: score
        """

        warning = 1
        fatal_error = 2
        verbose = True

        error_score = 0

        # handle fatal errors
        found_ids = find_invalid_ref_of_traffic_lights(scenario)
        if found_ids and verbose:
            error_score = max(error_score, fatal_error)
            self.mwindow_ui.crdesigner_console_wrapper.text_browser.append(
                "invalid traffic light refs: " + str(found_ids))
            QMessageBox.critical(self.mwindow_ui, "CommonRoad XML error",
                                 "Scenario contains invalid traffic light refenence(s): " + str(found_ids),
                                 QMessageBox.Ok, )

        found_ids = find_invalid_ref_of_traffic_signs(scenario)
        if found_ids and verbose:
            error_score = max(error_score, fatal_error)
            self.mwindow_ui.crdesigner_console_wrapper.text_browser.append(
                "invalid traffic sign refs: " + str(found_ids))
            QMessageBox.critical(self.mwindow_ui, "CommonRoad XML error",
                                 "Scenario contains invalid traffic sign refenence(s): " + str(found_ids),
                                 QMessageBox.Ok, )

        if error_score >= fatal_error:
            return error_score

        # handle warnings
        found_ids = find_invalid_lanelet_polygons(scenario)
        if found_ids and verbose:
            error_score = max(error_score, warning)
            self.mwindow_ui.crdesigner_console_wrapper.text_browser.append(
                    "Warning: Lanelet(s) with invalid polygon:" + str(found_ids))
            QMessageBox.warning(self.mwindow_ui, "CommonRoad XML error",
                                "Scenario contains lanelet(s) with invalid polygon: " + str(found_ids),
                                QMessageBox.Ok, )

        return error_score

    def close_event(self, event):
        """
        See how to move this bad boy into the service layer.
        """
        event.ignore()
        self.mwindow_ui.close_window()

