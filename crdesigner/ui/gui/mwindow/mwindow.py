from crdesigner.ui.gui.mwindow.service_layer import config
from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.animated_viewer_wrapper import AnimatedViewerWrapper
from crdesigner.ui.gui.mwindow.service_layer.gui_resources.MainWindow import Ui_mainWindow
from crdesigner.ui.gui.mwindow.service_layer.gui_resources.scenario_saving_dialog import ScenarioDialog
from crdesigner.ui.gui.mwindow.crdesigner_console_wrapper.crdesigner_console_wrapper import CRDesignerConsoleWrapper
from crdesigner.ui.gui.mwindow.service_layer.general_services import setup_tmp
from crdesigner.ui.gui.mwindow.service_layer.general_services import setup_mwindow
from crdesigner.ui.gui.mwindow.service_layer.general_services import center
from crdesigner.ui.gui.mwindow.service_layer.general_services import close_window
from crdesigner.ui.gui.mwindow.service_layer.config import MWINDOW_TMP_FOLDER_PATH
from crdesigner.ui.gui.mwindow.service_layer.general_services import update_max_step_service_layer
from crdesigner.ui.gui.mwindow.service_layer.general_services import store_scenario_service_layer
from crdesigner.ui.gui.mwindow.service_layer.general_services import update_toolbox_scenarios_service_layer
from crdesigner.ui.gui.mwindow.service_layer.general_services import check_scenario_service_layer
from crdesigner.ui.gui.mwindow.top_bar_wrapper.top_bar_wrapper import TopBarWrapper
from crdesigner.ui.gui.mwindow.toolboxes.road_network_toolbox.create_road_network_toolbox \
    import create_road_network_toolbox
from crdesigner.ui.gui.mwindow.toolboxes.converter_toolbox.create_converter_toolbox import create_converter_toolbox
from crdesigner.ui.gui.mwindow.toolboxes.obstacle_toolbox.create_obstacle_toolbox import create_obstacle_toolbox
from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.commonroad_viewer.service_layer.draw_params_updater import ColorSchema


import logging
from PyQt5.QtWidgets import *
from PyQt5 import QtGui
from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.gui_sumo_simulation import SUMO_AVAILABLE
if SUMO_AVAILABLE:
    pass
import yaml


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
        self.crdesigner_console_wrapper = None  # this can be removed
        self.play_activated = False
        self.viewer_dock = None
        self.sumo_settings = None
        self.gui_settings = None
        # init any objects here
        self.scenario_saving_dialog = ScenarioDialog()
        self.animated_viewer_wrapper = AnimatedViewerWrapper(mwindow=self)
        # call the setup methods in the service layer
        setup_tmp(tmp_folder_path=self.tmp_folder)
        setup_mwindow(self)
        self.crdesigner_console_wrapper = CRDesignerConsoleWrapper(mwindow=self)
        self.road_network_toolbox = create_road_network_toolbox(mwindow=self)
        self.obstacle_toolbox = create_obstacle_toolbox(mwindow=self)
        self.converter_toolbox = create_converter_toolbox(mwindow=self)
        self.top_bar_wrapper = TopBarWrapper(mwindow=self)
        # IMPORTANT: this has to be after the toolboxes, otherwise the handle used in the fileactions to the viewer_dock
        # gets lost (by the setCentralWidget method)
        self.animated_viewer_wrapper.create_viewer_dock()
        self.status = self.statusbar
        self.status.showMessage("Welcome to CR Scenario Designer")
        self.update_window()

        center(mwindow=self)
        if path:
            self.open_path(path)

    # below here the functionality of the mwindow, some

    def update_max_step(self, value: int = -1):
        """ Redirect to the service layer. """
        logging.info('update_max_step')
        update_max_step_service_layer(mwindow=self, value=value)

    def store_scenario(self):
        """ Redirect to the service layer. """
        store_scenario_service_layer(mwindow=self)

    def update_toolbox_scenarios(self):
        """ Redirect to the service layer. """
        update_toolbox_scenarios_service_layer(mwindow=self)

    # here are some actual functionalities which are either too small for sourcing out or cant be due to dependencies

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

        Redirect to the service layer.

        :return: score
        """
        return check_scenario_service_layer(mwindow=self, scenario=scenario)

    def colorscheme(self) -> ColorSchema:
        if config.DARKMODE:
            colorscheme = ColorSchema(axis=config.AXIS_VISIBLE, background='#303030', color='#f0f0f0',
                                      highlight='#1e9678', second_background='#2c2c2c')
        else:
            colorscheme = ColorSchema(axis=config.AXIS_VISIBLE)

        return colorscheme

    def update_window(self):
        p = QtGui.QPalette()
        p.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(self.colorscheme().background))
        p.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(self.colorscheme().second_background))
        p.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor(self.colorscheme().background))
        p.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor(self.colorscheme().color))
        p.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor(self.colorscheme().color))
        p.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor(self.colorscheme().color))
        p.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor(self.colorscheme().background))
        self.setPalette(p)

        self.road_network_toolbox.road_network_toolbox_ui.update_window()
        self.obstacle_toolbox.obstacle_toolbox_ui.update_window()
        self.converter_toolbox.converter_toolbox.update_window()
        self.animated_viewer_wrapper.update_window()
        self.menubar.setStyleSheet('background-color: '+ self.colorscheme().second_background + '; color: ' + self.colorscheme().color)
