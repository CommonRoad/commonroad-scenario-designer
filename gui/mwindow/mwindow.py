import logging
import os
import pathlib
import sys
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import copy
from typing import Union
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from crdesigner.input_output.gui.gui_resources.MainWindow import Ui_mainWindow
from crdesigner.input_output.gui.gui_resources.scenario_saving_dialog import ScenarioDialog
from crdesigner.input_output.gui.misc.commonroad_viewer import AnimatedViewer
from gui.CONSTANTS import *
from mwindow_controller import *


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
        self.console = None
        self.play_activated = False
        self.text_browser = None
        self.viewer_dock = None
        self.sumo_settings = None
        self.gui_settings = None

        # init any objects here
        self.scenario_saving_dialog = ScenarioDialog()
        self.cr_viewer = AnimatedViewer(self, self.viewer_callback)

        # call the setup methods in the controller
        setup_tmp(tmp_folder_path=self.tmp_folder)
        setup_mwindow(self)
        create_file_actions()

