import os
import pathlib
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox

from crdesigner.common.config.gui_config import gui_config
from crdesigner.common.logging import logger
from crdesigner.common.sumo_available import SUMO_AVAILABLE
from crdesigner.ui.gui.autosaves.autosaves_setup import DIR_AUTOSAVE
from crdesigner.ui.gui.controller.animated_viewer.animated_viewer_wrapper_controller import (
    AnimatedViewerWrapperController,
)
from crdesigner.ui.gui.controller.settings.scenario_saving_dialog_controller import (
    ScenarioSavingDialogController,
)
from crdesigner.ui.gui.controller.settings.settings_controller import SettingsController
from crdesigner.ui.gui.controller.toolboxes.converter_toolbox.map_conversion_controller import (
    MapConversionToolboxController,
)
from crdesigner.ui.gui.controller.toolboxes.obstacle_toolbox.obstacle_controller import (
    ObstacleController,
)
from crdesigner.ui.gui.controller.toolboxes.road_network_toolbox.road_network_controller import (
    RoadNetworkController,
)
from crdesigner.ui.gui.controller.toolboxes.scenario_toolbox.scenario_toolbox_controller import (
    ScenarioToolboxController,
)
from crdesigner.ui.gui.controller.top_bar.top_bar_controller import TopBarController
from crdesigner.ui.gui.model.planning_problem_set_model import PlanningProblemSetModel
from crdesigner.ui.gui.model.scenario_model import ScenarioModel
from crdesigner.ui.gui.utilities.file_actions import open_commonroad_file
from crdesigner.ui.gui.utilities.util import (
    find_invalid_lanelet_polygons,
    find_invalid_ref_of_traffic_lights,
    find_invalid_ref_of_traffic_signs,
)
from crdesigner.ui.gui.view.console.console_ui import ConsoleUI
from crdesigner.ui.gui.view.mwindow_ui import MWindowUI


def setup_tmp(tmp_folder_path: str):
    """
    Set up the tmp folder of the MWindow at the given Path.
    """
    pathlib.Path(tmp_folder_path).mkdir(parents=True, exist_ok=True)


class MWindowController:
    """Controller for the main window of the GUI."""

    def __init__(self, test: bool = False):
        """
        Constructor of the main window controller.

        :param test: Boolean indicating whether called from test case.
        """
        # init or set all attributes here
        self._test = test
        self.tmp_folder = gui_config.MWINDOW_TMP_FOLDER_PATH
        self.filename = None
        self.slider_clicked = False
        self.play_activated = False
        self.path_autosave = DIR_AUTOSAVE + "/autosave.xml"
        self.path_logging = DIR_AUTOSAVE + "/logging_file.txt"

        # init scenario model
        self.scenario_model = ScenarioModel()
        self.pps_model = PlanningProblemSetModel()

        # init any objects here
        self.scenario_saving_dialog = ScenarioSavingDialogController(
            self.scenario_model, self.pps_model
        )
        # scenario_model is given

        # call the setup methods in the service layer
        setup_tmp(tmp_folder_path=self.tmp_folder)

        # init UI
        self.mwindow_ui = MWindowUI()
        self.mwindow_ui.closeEvent = self.close_event

        self.animated_viewer_wrapper = AnimatedViewerWrapperController(
            mwindow=self,
            scenario_model=self.scenario_model,
            scenario_saving_dialog=self.scenario_saving_dialog,
        )
        self.mwindow_ui.animated_viewer_wrapper = self.animated_viewer_wrapper
        self.animated_viewer_wrapper.create_viewer_dock()

        # call the setup methods in the service layer
        self.crdesigner_console_wrapper = ConsoleUI(mwindow=self)
        self.mwindow_ui.crdesigner_console_wrapper = self.crdesigner_console_wrapper

        self.road_network_toolbox = RoadNetworkController(mwindow=self)
        self.mwindow_ui.addDockWidget(
            Qt.DockWidgetArea.LeftDockWidgetArea, self.road_network_toolbox
        )
        self.mwindow_ui.road_network_toolbox = self.road_network_toolbox

        self.obstacle_toolbox = ObstacleController(mwindow=self)
        self.mwindow_ui.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.obstacle_toolbox)
        self.mwindow_ui.obstacle_toolbox = self.obstacle_toolbox

        self.map_converter_toolbox = MapConversionToolboxController(mwindow=self)
        self.mwindow_ui.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea, self.map_converter_toolbox
        )
        self.mwindow_ui.map_converter_toolbox = self.map_converter_toolbox

        self.scenario_toolbox = ScenarioToolboxController(mwindow=self)
        self.mwindow_ui.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.scenario_toolbox)
        self.mwindow_ui.scenario_toolbox = self.scenario_toolbox

        self.mwindow_ui.top_bar = TopBarController(self)
        self.settings = SettingsController(self)

        # IMPORTANT: this has to be after the toolboxes, otherwise the handle used in the fileactions to the viewer_dock
        # gets lost (by the setCentralWidget method)
        self.animated_viewer_wrapper.create_viewer_dock()
        self.status = self.mwindow_ui.statusbar
        self.status.showMessage("Welcome to CR Scenario Designer")

        self.check_for_auto_saved_file()
        self.mwindow_ui.update_window()
        self.center()

    def check_for_auto_saved_file(self) -> None:
        """
        Check for the existence of an auto saved file and handles it accordingly.
        As well it handles the events fpr the logging file.
        """
        if os.path.exists(self.path_autosave):
            reply = self.mwindow_ui.ask_for_autosaved_file()
            if reply == QMessageBox.StandardButton.Save:
                self.directory = QFileDialog.getExistingDirectory(
                    self.scenario_saving_dialog.save_window,
                    "Dir",
                    options=QFileDialog.Option.ShowDirsOnly,
                )
                if self.directory:
                    if os.path.exists(self.path_logging):
                        time = datetime.now()
                        with (
                            open(self.path_logging, "r") as fp1,
                            open(
                                self.directory
                                + "/logging_file_"
                                + time.strftime("%d-%b-%y %H:%M:%S"),
                                "w",
                            ) as fp2,
                        ):
                            results = fp1.read()
                            fp2.write(results)
                reply = self.mwindow_ui.ask_for_autosaved_file(False)

            if reply == QMessageBox.StandardButton.Yes:
                open_commonroad_file(self, self.path_autosave)
                self.road_network_toolbox.initialize_road_network_toolbox()
                self.obstacle_toolbox.obstacle_toolbox_ui.initialize_obstacle_information()
            elif reply == QMessageBox.StandardButton.No:
                os.remove(self.path_autosave)

        if os.path.exists(self.path_logging):
            os.remove(self.path_logging)
        logger.set_initialized()

    def check_scenario(self, scenario) -> int:
        """
        Check the scenario to validity and calculate a quality score.
        The higher the score the higher the data faults.

        Redirect to the service layer.

        :return: score
        """
        return self.check_scenario_service_layer(scenario=scenario)

    def center(self):
        """Function that makes sure the main window is in the center of screen."""
        screen = QGuiApplication.primaryScreen().availableGeometry()
        size = self.mwindow_ui.geometry()
        self.mwindow_ui.move(
            int((screen.width() - size.width()) / 2), int((screen.height() - size.height()) / 2)
        )

    # TODO: MODEL
    def store_scenario_service_layer(self):
        """Store the current scenario in the view in the scenario model."""
        scenario = self.mwindow_ui.animated_viewer_wrapper.cr_viewer.current_scenario
        self.scenario_model.set_scenario(scenario)

        # TODO: move as signal update  # self.mwindow_ui.update_toolbox_scenarios()

    def update_toolbox_scenarios_service_layer(self):
        # TODO: Update to scenario_model
        scenario = self.mwindow_ui.animated_viewer_wrapper.cr_viewer.current_scenario
        if SUMO_AVAILABLE:
            self.mwindow_ui.obstacle_toolbox.sumo_simulation.scenario = scenario
            self.mwindow_ui.map_converter_toolbox.sumo_simulation.scenario = scenario

    def store_scenario(self):
        """Redirect to the service layer."""
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
                "invalid traffic light refs: " + str(found_ids)
            )
            QMessageBox.critical(
                self.mwindow_ui,
                "CommonRoad XML error",
                "Scenario contains invalid traffic light refenence(s): " + str(found_ids),
                QMessageBox.StandardButton.Ok,
            )

        found_ids = find_invalid_ref_of_traffic_signs(scenario)
        if found_ids and verbose:
            error_score = max(error_score, fatal_error)
            self.mwindow_ui.crdesigner_console_wrapper.text_browser.append(
                "invalid traffic sign refs: " + str(found_ids)
            )
            QMessageBox.critical(
                self.mwindow_ui,
                "CommonRoad XML error",
                "Scenario contains invalid traffic sign refenence(s): " + str(found_ids),
                QMessageBox.StandardButton.Ok,
            )

        if error_score >= fatal_error:
            return error_score

        # handle warnings
        found_ids = find_invalid_lanelet_polygons(scenario)
        if found_ids and verbose:
            error_score = max(error_score, warning)
            self.mwindow_ui.crdesigner_console_wrapper.text_browser.append(
                "Warning: Lanelet(s) with invalid polygon:" + str(found_ids)
            )
            QMessageBox.warning(
                self.mwindow_ui,
                "CommonRoad XML error",
                "Scenario contains lanelet(s) with invalid polygon: " + str(found_ids),
                QMessageBox.StandardButton.Ok,
            )

        return error_score

    def close_event(self, event):
        """
        Closes the app and deletes the autosaved file
        """
        event.ignore()
        close_app = self.mwindow_ui.close_window() if not self._test else True
        if close_app:
            if os.path.exists(self.path_autosave):
                os.remove(self.path_autosave)
            QApplication.quit()
