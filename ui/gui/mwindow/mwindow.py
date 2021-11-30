from commonroad.scenario.lanelet import Lanelet
from commonroad.scenario.obstacle import Obstacle
from ui.gui.mwindow.service_layer.gui_resources.MainWindow import Ui_mainWindow
from ui.gui.mwindow.service_layer.gui_resources.scenario_saving_dialog import ScenarioDialog
from ui.gui.mwindow.animated_viewer_wrapper.commonroad_viewer import AnimatedViewer
from ui.gui.mwindow.service_layer import config
from ui.gui.mwindow.console_wrapper.console_wrapper import ConsoleWrapper
from ui.gui.mwindow.service_layer.general_services import setup_tmp
from ui.gui.mwindow.service_layer.general_services import setup_mwindow
from ui.gui.mwindow.service_layer.general_services import center
from ui.gui.mwindow.service_layer.file_actions import close_window
# these were moved to the topbar
#from ui.gui.mwindow.mwindow_service_layer.file_actions import create_file_actions
#from ui.gui.mwindow.mwindow_service_layer.setting_actions import create_setting_actions
#from ui.gui.mwindow.mwindow_service_layer.help_actions import create_help_actions
from ui.gui.mwindow.top_bar_wrapper.top_bar_wrapper import TopBarWrapper
from ui.gui.mwindow.toolboxes.road_network_toolbox.create_road_network_toolbox import create_road_network_toolbox
from ui.gui.mwindow.toolboxes.converter_toolbox.create_converter_toolbox import create_converter_toolbox
from ui.gui.mwindow.toolboxes.obstacle_toolbox.create_obstacle_toolbox import create_obstacle_toolbox
# these were moved to the top_bar
#from ui.gui.mwindow.mwindow_service_layer.file_actions import file_new
#from ui.gui.mwindow.mwindow_service_layer.file_actions import open_commonroad_file
#from ui.gui.mwindow.mwindow_service_layer.file_actions import file_save
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from meta.CONSTANTS import *
from ui.gui.mwindow.service_layer.util import *
# replaces menubar and topbar

from typing import Union
import logging
import copy
from PyQt5.QtWidgets import *
from ui.gui.mwindow.animated_viewer_wrapper.gui_sumo_simulation import SUMO_AVAILABLE
if SUMO_AVAILABLE:
    pass


class MWindow(QMainWindow, Ui_mainWindow):
    """The Main window of the CR Scenario Designer."""

    def __init__(self, path=None):
        super().__init__()
        # init or set all attributes here
        self.tmp_folder = MWINDOW_TMP_FOLDER_PATH
        self.filename = None
        self.slider_clicked = False
        # Scenario + Lanelet variables
        self.scenarios = []
        self.current_scenario_index = -1
        # GUI attributes
        self.road_network_toolbox = None
        self.obstacle_toolbox = None
        self.map_converter_toolbox = None
        self.console_wrapper = None  # this can be removed
        self.play_activated = False
        #self.text_browser = None  # handle to the text browser in the console ->  TODO remove this (this is left here for visibility as a reminder)
        self.viewer_dock = None
        self.sumo_settings = None
        self.gui_settings = None

        # init any objects here
        # TODO make an own package for these two later
        self.scenario_saving_dialog = ScenarioDialog()
        self.cr_viewer = AnimatedViewer(self, self.viewer_callback)

        # call the setup methods in the service layer
        setup_tmp(tmp_folder_path=self.tmp_folder)
        setup_mwindow(self)
        self.create_viewer_dock()
        self.console_wrapper = ConsoleWrapper(mwindow=self)

        self.road_network_toolbox = create_road_network_toolbox(mwindow=self)
        self.obstacle_toolbox = create_obstacle_toolbox(mwindow=self)
        self.converter_toolbox = create_converter_toolbox(mwindow=self)
        self.top_bar_wrapper = TopBarWrapper(mwindow=self)
        self.status = self.statusbar
        self.status.showMessage("Welcome to CR Scenario Designer")

        center(mwindow=self)
        if path:
            self.open_path(path)

        #self.fileNewAction, self.fileOpenAction, self.separator, self.fileSaveAction, self.exitAction = create_file_actions(mwindow=self)
        #self.osm_settings, self.opendrive_settings, self.gui_settings, self.sumo_settings = create_setting_actions(mwindow=self)
        #self.open_web, self.open_forum = create_help_actions(mwindow=self)


        # init the wrapper classes
        # this was replaced: self.console_wrapper, self.text_browser = create_console(mwindow=self)
        #self.toolbar_wrapper = ToolBarWrapper(mwindow=self, file_new=file_new,open_commonroad_file=open_commonroad_file, file_save=file_save)

        # instanciate the menu bar
        #self.menu_bar_wrapper = MenuBarWrapper(mwindow=self,
        #                        fileNewAction=self.fileNewAction, fileOpenAction=self.fileOpenAction,
        #                        separator=self.separator, exitAction=self.exitAction, gui_settings=self.gui_settings,
        #                        sumo_settings=self.sumo_settings, osm_settings=self.osm_settings,
        #                        open_web=self.open_web, open_forum=self.open_forum, fileSaveAction=self.fileSaveAction
        #                        )


    # below here the functionality of the mwindow

    def viewer_callback(self, selected_object: Union[Lanelet, Obstacle], output: str):
        """
            TODO find out what this method does.
        """
        if isinstance(selected_object, Lanelet):
            self.road_network_toolbox.road_network_toolbox.selected_lanelet_two.setCurrentText(
                    self.road_network_toolbox.road_network_toolbox.selected_lanelet_one.currentText())
            self.road_network_toolbox.road_network_toolbox.selected_lanelet_one.setCurrentText(
                    str(selected_object.lanelet_id))
            self.road_network_toolbox.road_network_toolbox.selected_lanelet_update.setCurrentText(
                    str(selected_object.lanelet_id))
        elif isinstance(selected_object, Obstacle):
            self.obstacle_toolbox.obstacle_toolbox.selected_obstacle.setCurrentText(str(selected_object.obstacle_id))
        if output != "":
            self.console_wrapper.text_browser.append(output)

    def create_viewer_dock(self):
        """Create the viewer dock."""
        self.viewer_dock = QWidget(self)
        toolbar = NavigationToolbar(self.cr_viewer.dynamic, self.viewer_dock)
        layout = QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.cr_viewer.dynamic)
        self.viewer_dock.setLayout(layout)
        self.setCentralWidget(self.viewer_dock)

    def update_view(self, focus_on_network=None):
        """ update all components."""
        # reset selection of all other selectable elements
        if self.cr_viewer.current_scenario is None:
            return
        if focus_on_network is None:
            focus_on_network = config.AUTOFOCUS
        self.cr_viewer.update_plot(focus_on_network=focus_on_network)

    def toolbox_callback(self, scenario):
        """
        TODO find out why this is here.
        """
        if scenario is not None:
            self.cr_viewer.open_scenario(scenario)
            self.update_view(focus_on_network=True)
            self.update_max_step()
            self.store_scenario()

    def update_max_step(self, value: int = -1):
        """
        Update the max steps.
        """
        logging.info('update_max_step')
        value = value if value > -1 else self.cr_viewer.max_timestep
        self.top_bar_wrapper.toolbar_wrapper.label2.setText(' / ' + str(value))
        self.top_bar_wrapper.toolbar_wrapper.slider.setMaximum(value)

    def store_scenario(self):
        self.scenarios.append(copy.deepcopy(self.cr_viewer.current_scenario))
        self.current_scenario_index += 1
        self.update_toolbox_scenarios()

    def update_toolbox_scenarios(self):
        scenario = self.cr_viewer.current_scenario
        self.road_network_toolbox.refresh_toolbox(scenario)
        self.obstacle_toolbox.refresh_toolbox(scenario)
        self.map_converter_toolbox.refresh_toolbox(scenario)
        if SUMO_AVAILABLE:
            self.obstacle_toolbox.sumo_simulation.scenario = scenario
            self.map_converter_toolbox.sumo_simulation.scenario = scenario

    def closeEvent(self, event):
        """
        See how to move this bad boy into the service layer.
        """
        event.ignore()
        close_window(mwindow=self)

    def process_trigger(self, q):
        self.status.showMessage(q.text() + ' is triggered')

    def initialize_toolboxes(self):
        self.road_network_toolbox.initialize_toolbox()
        self.obstacle_toolbox.initialize_toolbox()

    def check_scenario(self, scenario) -> int:
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
            self.text_browser.append("invalid traffic light refs: " +
                                     str(found_ids))
            QMessageBox.critical(
                self,
                "CommonRoad XML error",
                "Scenario contains invalid traffic light refenence(s): " +
                str(found_ids),
                QMessageBox.Ok,
            )

        found_ids = find_invalid_ref_of_traffic_signs(scenario)
        if found_ids and verbose:
            error_score = max(error_score, fatal_error)
            self.text_browser.append("invalid traffic sign refs: " +
                                     str(found_ids))
            QMessageBox.critical(
                self,
                "CommonRoad XML error",
                "Scenario contains invalid traffic sign refenence(s): " +
                str(found_ids),
                QMessageBox.Ok,
            )

        if error_score >= fatal_error:
            return error_score

        # handle warnings
        found_ids = find_invalid_lanelet_polygons(scenario)
        if found_ids and verbose:
            error_score = max(error_score, warning)
            self.text_browser.append(
                "Warning: Lanelet(s) with invalid polygon:" + str(found_ids))
            QMessageBox.warning(
                self,
                "CommonRoad XML error",
                "Scenario contains lanelet(s) with invalid polygon: " +
                str(found_ids),
                QMessageBox.Ok,
            )

        return error_score
